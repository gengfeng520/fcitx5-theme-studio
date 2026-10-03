"""Fcitx5 theme rendering and export, independent of the editor UI."""
from PyQt6.QtGui import QColor,QPainter,QPixmap,QPainterPath,QPen,QFont,QFontMetrics
from PyQt6.QtCore import Qt,QRectF

DEFAULT=dict(bg='#e2efff',fg='#182635',accent='#4084c8',opacity=85,radius=18,gap=8,size=16,selected_fg='#ffffff',highlight=True,highlight_opacity=100,image_mode='cover',zoom=100,pan_x=50,pan_y=50,image_width=580,image_height=150,background_style='stable',anchor='TopRight',preview_width=480,preview_height=90,fit_candidate_height=True,preview_preedit=False,image_dx=0.0,image_dy=0.0,picture_space=160,edge_fill=True,separate_candidates=True)

def content_margins(s,has_picture):
    margin=max(8,s['radius']);left=right=margin
    if has_picture and s['background_style']=='stable' and s['separate_candidates']:
        if s['anchor']=='TopRight':right+=s['picture_space']
        elif s['anchor']=='TopLeft':left+=s['picture_space']
    return left,right

def config_text(s,has_picture=True):
    gravity={'TopRight':'Top Right','TopLeft':'Top Left','Center':'Center'}[s['anchor']]
    left,right=content_margins(s,has_picture)
    content=f'[InputPanel/ContentMargin]\nLeft={left}\nRight={right}\nTop={max(8,s["radius"])}\nBottom={max(8,s["radius"])}\n'
    clip_y=1 if s['edge_fill'] and s['background_style']=='stable' else s['radius']
    clip=f'[InputPanel/Background/OverlayClipMargin]\nLeft={s["radius"]}\nRight={s["radius"]}\nTop={clip_y}\nBottom={clip_y}\n'
    def margins(section,n): return f'[{section}]\nLeft={n}\nRight={n}\nTop={n}\nBottom={n}\n'
    return (f'[Metadata]\nName=Theme Studio\nVersion=1\nDescription=Local static theme\nScaleWithDPI=True\n\n[InputPanel]\nNormalColor={s["fg"]}\nHighlightColor={s["selected_fg"]}\nHighlightCandidateColor={s["selected_fg"]}\nHighlightBackgroundColor=#00000000\n\n[InputPanel/Background]\nImage=background.png\nOverlay={"picture.png" if s['background_style']=='stable' else ""}\nGravity={gravity}\nHideOverlayIfOversize=False\n\n'+clip+'\n'+margins('InputPanel/Background/Margin',max(1,s['radius']))+'\n'+content+'\n'+margins('InputPanel/TextMargin',s['gap'])+f'\n[InputPanel/Highlight]\nColor={highlight_color(s)}\nBorderColor=#00000000\nBorderWidth=0\n')

def highlight_color(s):
    alpha=round(255*s['highlight_opacity']/100) if s['highlight'] else 0
    return s['accent']+f'{alpha:02x}'

def image_rect(s,picture,w,h):
    iw,ih=picture.width(),picture.height()
    if s['image_mode']=='stretch':dw,dh=w*s['zoom']/100,h*s['zoom']/100
    else:
        scale=(max if s['image_mode']=='cover' else min)(w/iw,h/ih)*s['zoom']/100
        dw,dh=iw*scale,ih*scale
    return QRectF((w-dw)*s['pan_x']/100+s.get('image_dx',0),(h-dh)*s['pan_y']/100+s.get('image_dy',0),dw,dh)

def image_layer(s,picture,target_height=None):
    w,h=s['image_width'],s['image_height'];pix=QPixmap(w,h);pix.fill(Qt.GlobalColor.transparent)
    if picture and not picture.isNull():
        p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);p.setOpacity(s['opacity']/100)
        p.drawPixmap(image_rect(s,picture,w,h),picture,QRectF(picture.rect()));p.end()
    if s.get('fit_candidate_height',True):
        font=QFont('Sans');font.setPointSize(s['size']);height=QFontMetrics(font).height()+2*s['gap']
        if s['edge_fill']:height=target_height or height+2*max(8,s['radius'])
        pix=pix.scaledToHeight(height,Qt.TransformationMode.SmoothTransformation)
    # Keep the subject inside the same inset used by OverlayClipMargin.
    # Padding is added after fitting so the image itself keeps its chosen size.
    inset=s['radius'] if s['background_style']=='stable' else 0
    inset_y=0 if s['edge_fill'] else inset
    if inset:
        padded=QPixmap(pix.width()+2*inset,pix.height()+2*inset_y);padded.fill(Qt.GlobalColor.transparent)
        p=QPainter(padded);p.drawPixmap(inset,inset_y,pix);p.end();pix=padded
    return pix

def overlay_position(s,w,h,lw,lh):
    x=0 if s['anchor']=='TopLeft' else w-lw if s['anchor']=='TopRight' else (w-lw)/2
    y=(h-lh)/2 if s['anchor']=='Center' else 0
    return int(x),int(y)

def background(s,picture=None,w=320,h=160):
    pix=QPixmap(w,h);pix.fill(Qt.GlobalColor.transparent)
    p=QPainter(pix);p.setRenderHint(QPainter.RenderHint.Antialiasing)
    path=QPainterPath();path.addRoundedRect(QRectF(1,1,w-2,h-2),s['radius'],s['radius']);p.setClipPath(path)
    p.setOpacity(s['opacity']/100);p.fillRect(pix.rect(),QColor(s['bg']))
    p.setOpacity(0.6);p.setPen(QPen(QColor('white'),1));p.drawPath(path)
    if picture and not picture.isNull():
        p.setOpacity(1)
        if s['background_style']=='rounded':
            p.setOpacity(s['opacity']/100);p.drawPixmap(image_rect(s,picture,w,h),picture,QRectF(picture.rect()))
        else:
            r=s['radius'];ry=1 if s['edge_fill'] else r;p.setClipping(False);p.setClipRect(QRectF(r,ry,w-2*r,h-2*ry))
            layer=image_layer(s,picture,h);x,y=overlay_position(s,w,h,layer.width(),layer.height());p.drawPixmap(x,y,layer)
    p.end();return pix

def theme_preview(s,picture,w,h):
    if s['background_style']=='stable':return background(s,picture,w,h)
    source=background(s,picture,s['image_width'],s['image_height']);out=QPixmap(w,h);out.fill(Qt.GlobalColor.transparent);p=QPainter(out)
    r=max(1,s['radius']);sx=[0,r,source.width()-r,source.width()];sy=[0,r,source.height()-r,source.height()];dx=[0,r,w-r,w];dy=[0,r,h-r,h]
    for row in range(3):
        for col in range(3):p.drawPixmap(QRectF(dx[col],dy[row],dx[col+1]-dx[col],dy[row+1]-dy[row]),source,QRectF(sx[col],sy[row],sx[col+1]-sx[col],sy[row+1]-sy[row]))
    p.end();return out

