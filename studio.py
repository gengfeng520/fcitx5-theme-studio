#!/usr/bin/python3
"""Local, static Fcitx5 theme editor. No input content is read."""
import sys, os, json, shutil, subprocess, re
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (QApplication,QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QSlider,QColorDialog,QFileDialog,QMessageBox,QComboBox,QCheckBox,QScrollArea,QLineEdit,QSplitter,QDoubleSpinBox,QFrame,QTabWidget,QGridLayout,QStackedWidget,QListWidget,QListWidgetItem,QPlainTextEdit,QSizePolicy)
from PyQt6.QtGui import QColor,QPainter,QPixmap,QPainterPath,QPen,QFont,QFontMetrics,QIcon,QLinearGradient,QRadialGradient
from PyQt6.QtCore import Qt,QRectF,QPointF,QSize

from theme_engine import (DEFAULT,content_margins,config_text,highlight_color,image_rect,image_layer,overlay_position,background,theme_preview)

class PreviewLabel(QLabel):
    def __init__(self):
        super().__init__();self.source=None;self.setMinimumSize(1,1);self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Ignored);self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    def set_source(self,pix):
        self.source=pix;self.fit_image()
    def fit_image(self):
        if self.source is None:return
        size=QSize(max(1,self.width()-8),max(1,self.height()-8))
        self.setPixmap(self.source.scaled(size,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation) if self.source.width()>size.width() or self.source.height()>size.height() else self.source)
    def resizeEvent(self,event):
        super().resizeEvent(event);self.fit_image()

class ImageEditor(QWidget):
    def __init__(self,studio):
        super().__init__();self.studio=studio;self.last=None;self.setMinimumSize(260,80);self.setMouseTracking(True);self.setCursor(Qt.CursorShape.OpenHandCursor)
    def geometry_map(self):
        s=self.studio.s;scale=min((self.width()-40)/s['image_width'],(self.height()-40)/s['image_height'])
        return scale,QPointF((self.width()-s['image_width']*scale)/2,(self.height()-s['image_height']*scale)/2)
    def paintEvent(self,event):
        p=QPainter(self);p.fillRect(self.rect(),QColor('#263349' if getattr(self.studio,'ui_mode','day')=='night' else '#e8effa'));scale,origin=self.geometry_map();p.translate(origin);p.scale(scale,scale);s=self.studio.s;w,h=s['image_width'],s['image_height'];canvas=QRectF(0,0,w,h)
        p.fillRect(canvas,QColor(s['bg']));pic=self.studio.picture
        if pic and not pic.isNull():
            rect=image_rect(s,pic,w,h);p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform);p.save();p.setClipRect(canvas);p.drawPixmap(rect,pic,QRectF(pic.rect()));p.restore()
        p.setPen(QPen(QColor('#5483e0'),2/scale,Qt.PenStyle.DashLine));p.drawRect(canvas);p.end()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton and self.studio.picture:self.last=event.position();self.setCursor(Qt.CursorShape.ClosedHandCursor)
    def mouseMoveEvent(self,event):
        if self.last is None:return
        scale,_=self.geometry_map();delta=(event.position()-self.last)/scale;self.last=event.position();s=self.studio.s;s['image_dx']+=delta.x();s['image_dy']+=delta.y();self.studio.refresh()
    def mouseReleaseEvent(self,event):self.last=None;self.setCursor(Qt.CursorShape.OpenHandCursor)
    def wheelEvent(self,event):
        if not self.studio.picture:return
        s=self.studio.s;factor=1.1 if event.angleDelta().y()>0 else 1/1.1
        self.studio.change('zoom',max(10,min(300,round(s['zoom']*factor))));event.accept()



class Studio(QWidget):
    def __init__(self):
        super().__init__()
        self.s=DEFAULT.copy();self.picture=None;self.picture_path=''
        self.colors={};self.sliders={};self.offsets={}
        self.setWindowTitle('Fcitx5 Theme Studio · 皮肤工坊');self.resize(1120,760);self.setMinimumSize(920,640)
        self.setWindowIcon(QIcon(str(Path(__file__).parent/'assets/icon.svg')))
        self.ui_mode='day'
        self.set_mode('day',persist=False)
        outer=QVBoxLayout(self);outer.setContentsMargins(20,14,20,14);outer.setSpacing(12)
        header=QHBoxLayout();leftmark=QLabel('本地创作 · Fcitx5');leftmark.setObjectName('muted');leftmark.setFixedWidth(150);header.addWidget(leftmark)
        titles=QVBoxLayout();title=QLabel('皮肤工坊');title.setObjectName('title');title.setAlignment(Qt.AlignmentFlag.AlignCenter);titles.addWidget(title)
        sub=QLabel('让每一次输入，都有你的风格');sub.setObjectName('muted');sub.setAlignment(Qt.AlignmentFlag.AlignCenter);titles.addWidget(sub);header.addLayout(titles,1)
        self.mode_switch=QComboBox();self.mode_switch.addItem('☀  日间模式','day');self.mode_switch.addItem('☾  夜间模式','night');self.mode_switch.setFixedWidth(150);self.mode_switch.currentIndexChanged.connect(lambda _:self.safe(lambda:self.set_mode(self.mode_switch.currentData())));header.addWidget(self.mode_switch);outer.addLayout(header)
        split=QSplitter(Qt.Orientation.Horizontal);outer.addWidget(split,1)
        left=QWidget();leftbox=QVBoxLayout(left);leftbox.setContentsMargins(0,0,0,0);leftbox.setSpacing(12);split.addWidget(left)
        tabs=QTabWidget();self.tabs=tabs;leftbox.addWidget(tabs,1)
        basic=QWidget();self.root=QVBoxLayout(basic);self.root.setContentsMargins(12,14,12,14);self.root.setSpacing(12)
        advanced=QWidget();self.advanced=QVBoxLayout(advanced);self.advanced.setContentsMargins(12,14,12,14);self.advanced.setSpacing(12)
        for title,body in [('常用设置',basic),('高级设置',advanced)]:
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(body);tabs.addTab(scroll,title)
        def card(parent,title):
            frame=QFrame();frame.setObjectName('card');layout=QVBoxLayout(frame);layout.setContentsMargins(16,14,16,16);layout.setSpacing(10)
            label=QLabel(title);label.setObjectName('heading');layout.addWidget(label);parent.addWidget(frame);return layout
        def label(parent,text):
            item=QLabel(text);item.setObjectName('muted');item.setWordWrap(True);parent.addWidget(item);return item
        def slider(parent,key,title,low,high):
            row=QHBoxLayout();name=QLabel();name.setFixedWidth(138);control=QSlider(Qt.Orientation.Horizontal);control.setRange(low,high)
            control.valueChanged.connect(lambda v,k=key:self.change(k,v));row.addWidget(name);row.addWidget(control,1);self.sliders[key]=(control,name,title);parent.addLayout(row)
        look=card(self.root,'01  配色与文字')
        presets=QHBoxLayout()
        for title,name in [('晴空','sky'),('夜色','night'),('纸白','paper')]:self.button(presets,title,lambda n=name:self.look_preset(n))
        look.addLayout(presets)
        palette=QGridLayout();palette.setHorizontalSpacing(10);palette.setVerticalSpacing(8)
        for index,(key,title) in enumerate([('bg','背景'),('fg','文字'),('accent','选中背景'),('selected_fg','选中文字')]):
            cell=QVBoxLayout();name=QLabel(title);name.setObjectName('muted');cell.addWidget(name)
            b=QPushButton();b.setProperty('swatch',True);b.setToolTip('点击选择颜色');b.clicked.connect(lambda _,k=key:self.color(k));cell.addWidget(b);self.colors[key]=b;palette.addLayout(cell,index//2,index%2)
        look.addLayout(palette)
        self.highlight=QCheckBox('突出显示选中的候选词');self.highlight.toggled.connect(lambda v:self.change('highlight',v));look.addWidget(self.highlight)
        for args in [('opacity','透明度',30,100),('radius','圆角',0,40),('size','文字大小',10,32)]:slider(look,*args)
        picture=card(self.root,'02  图片与间距')
        self.image_name=label(picture,'尚未选择图片 · 推荐透明 PNG')
        row=QHBoxLayout();self.button(row,'导入图片',self.image);self.button(row,'移除',self.clear);picture.addLayout(row)
        self.placement=QComboBox()
        for title,value in [('人物靠右','right'),('人物靠左','left'),('图片铺满背景','wallpaper')]:self.placement.addItem(title,value)
        self.placement.currentIndexChanged.connect(lambda _:self.choose_placement(self.placement.currentData()));picture.addWidget(self.placement)
        slider(picture,'zoom','图片大小',10,300)
        row=QHBoxLayout();row.addWidget(QLabel('人物区域宽度'));self.spacing=QDoubleSpinBox();self.spacing.setDecimals(0);self.spacing.setRange(0,600);self.spacing.setSingleStep(8);self.spacing.setSuffix(' px');self.spacing.valueChanged.connect(lambda v:self.change('picture_space',int(v)));row.addWidget(self.spacing);picture.addLayout(row)
        label(picture,'文字挡住人物时，增大人物区域宽度。图片的位置可以在右侧拖动调整。')
        self.edge=QCheckBox('人物上下贴边');self.edge.toggled.connect(lambda v:self.change('edge_fill',v));picture.addWidget(self.edge)
        row=QHBoxLayout();self.button(row,'重新对齐图片',self.align_picture);self.button(row,'拉开文字与人物',self.separate_picture);picture.addLayout(row)
        files=card(self.root,'03  保存与导出')
        row=QHBoxLayout();self.button(row,'保存设计',self.save);self.button(row,'载入设计',self.load);files.addLayout(row)
        row=QHBoxLayout();self.button(row,'导出主题',self.export);self.button(row,'恢复默认',self.reset);files.addLayout(row)
        label(files,'设计与图片一起保存在本地，也可到作品库保存命名作品。')
        self.root.addStretch()
        imageadv=card(self.advanced,'图片细节')
        self.style=QComboBox()
        for title,value in [('保持图片比例','stable'),('随圆角背景拉伸','rounded')]:self.style.addItem(title,value)
        self.style.currentIndexChanged.connect(lambda _:self.change('background_style',self.style.currentData()));imageadv.addWidget(self.style)
        self.anchor=QComboBox()
        for title,value in [('固定右侧','TopRight'),('固定左侧','TopLeft'),('居中','Center')]:self.anchor.addItem(title,value)
        self.anchor.currentIndexChanged.connect(lambda _:self.change('anchor',self.anchor.currentData()));imageadv.addWidget(self.anchor)
        self.separate=QCheckBox('为人物保留独立区域');self.separate.toggled.connect(lambda v:self.change('separate_candidates',v));imageadv.addWidget(self.separate)
        self.fit=QCheckBox('按单行候选框高度等比适配');self.fit.toggled.connect(lambda v:self.change('fit_candidate_height',v));imageadv.addWidget(self.fit)
        self.mode=QComboBox()
        for title,value in [('等比完整显示','contain'),('等比填满并裁剪','cover'),('拉伸铺满','stretch')]:self.mode.addItem(title,value)
        self.mode.currentIndexChanged.connect(lambda _:self.change('image_mode',self.mode.currentData()));imageadv.addWidget(self.mode)
        for args in [('pan_x','水平对齐',0,100),('pan_y','垂直对齐',0,100),('image_width','画布宽度',160,1200),('image_height','画布高度',80,500)]:slider(imageadv,*args)
        for key,title in [('image_dx','水平位移'),('image_dy','垂直位移')]:
            row=QHBoxLayout();row.addWidget(QLabel(title));spin=QDoubleSpinBox();spin.setRange(-100000,100000);spin.setDecimals(1);spin.setSuffix(' px');spin.valueChanged.connect(lambda v,k=key:self.change(k,v));row.addWidget(spin);self.offsets[key]=spin;imageadv.addLayout(row)
        previewadv=card(self.advanced,'文字与模拟预览')
        for args in [('gap','文字内间距',2,20),('highlight_opacity','选中背景浓淡',0,100),('preview_width','模拟宽度',180,600),('preview_height','模拟高度',70,180)]:slider(previewadv,*args)
        self.preedit=QCheckBox('预览显示拼音行');self.preedit.toggled.connect(lambda v:self.change('preview_preedit',v));previewadv.addWidget(self.preedit)
        label(previewadv,'真实候选框尺寸由候选词、字体和屏幕缩放决定。模拟预览供设计参考，最终请试打确认。')
        self.advanced.addStretch()
        self.button(leftbox,'应用到输入法',self.apply,'primary');self.button(leftbox,'恢复上一次应用前的主题',self.restore)
        rightbody=QWidget();split.addWidget(rightbody);self.right=QVBoxLayout(rightbody);self.right.setContentsMargins(4,4,4,4);self.right.setSpacing(12)
        edit=card(self.right,'设计画布')
        label(edit,'拖动移动 · 滚轮缩放 · 虚线内为导出范围')
        self.editor=ImageEditor(self);self.editor.setMinimumHeight(80);self.editor.setMaximumHeight(210);self.editor.setSizePolicy(QSizePolicy.Policy.Expanding,QSizePolicy.Policy.Expanding);edit.addWidget(self.editor,1)
        preview=card(self.right,'候选框预览')
        self.preview_selector=QComboBox();self.preview_selector.addItems(['短候选框','常规候选框','长候选框']);self.preview_selector.setCurrentIndex(1);preview.addWidget(self.preview_selector)
        self.preview_stack=QStackedWidget();self.preview_stack.setMinimumHeight(64);self.preview_stack.setMaximumHeight(180);preview.addWidget(self.preview_stack,1)
        self.previews=[];self.preview_pixmaps=[]
        for _ in range(3):
            item=PreviewLabel();self.preview_stack.addWidget(item);self.previews.append(item)
        self.preview=self.previews[1];self.preview_stack.setCurrentIndex(1);self.preview_selector.currentIndexChanged.connect(self.preview_stack.setCurrentIndex)
        label(preview,'大尺寸预览会缩小显示，主题导出尺寸保持不变。')
        typing=card(self.right,'试一试真实输入')
        self.test_input=QLineEdit();self.test_input.setPlaceholderText('输入拼音，查看系统候选框…');typing.addWidget(self.test_input)
        for layout in (edit,preview,typing):layout.setContentsMargins(14,10,14,10);layout.setSpacing(8)
        self.library_layout=self.build_library(tabs)
        split.setSizes([390,710])
        self.status=QLabel('就绪 · 先选配色或导入图片，再应用到输入法');self.status.setObjectName('status');self.status.setWordWrap(True);outer.addWidget(self.status)
        self.refresh()
        self.restore_session()
        self.refresh_library()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        dark=self.ui_mode=='night';gradient=QLinearGradient(0,0,self.width(),self.height())
        gradient.setColorAt(0,QColor('#172438' if dark else '#e5eefb'));gradient.setColorAt(.55,QColor('#20293c' if dark else '#f6f2fc'));gradient.setColorAt(1,QColor('#142f3b' if dark else '#def3f0'));p.fillRect(self.rect(),gradient)
        glow=QRadialGradient(self.width()*.74,self.height()*.18,self.width()*.55);glow.setColorAt(0,QColor(106,139,236,35 if dark else 45));glow.setColorAt(1,QColor(106,139,236,0));p.fillRect(self.rect(),glow);p.end()
    def set_mode(self,mode,persist=True):
        if mode not in ('day','night'):return
        self.ui_mode=mode;dark=mode=='night'
        fg='#e6edf9' if dark else '#24334a';muted='#a5b4cb' if dark else '#657892';border='rgba(173,196,236,35)' if dark else 'rgba(255,255,255,215)';card='rgba(38,51,73,210)' if dark else 'rgba(255,255,255,195)';control_border='#647c9d' if dark else '#a7b9d3';button_fill='#354964' if dark else '#e7eefb';button_hover='#466181' if dark else '#d7e5fc';field='rgba(17,30,49,190)' if dark else 'rgba(255,255,255,180)';accent='#91b5ff' if dark else '#3569dc'
        arrow=(Path(__file__).parent/'assets/chevron-down.svg').as_posix()
        self.setStyleSheet(f'''
            QWidget {{ color:{fg};font-family:"Noto Sans CJK SC","Sans";font-size:12px; }}
            Studio {{ background:transparent; }}
            QFrame#card {{ background:{card};border:1px solid {border};border-radius:16px; }}
            QLabel {{ background:transparent; }}
            QLabel#title {{ font-size:23px;font-weight:700; }}
            QLabel#heading {{ font-size:14px;font-weight:600; }}
            QLabel#muted {{ color:{muted}; }}
            QLabel#status {{ background:{card};padding:8px;border:1px solid {border};border-radius:10px;color:{muted}; }}
            QPushButton {{ background:{button_fill};border:1px solid {control_border};border-radius:9px;padding:7px 10px; }}
            QPushButton:hover {{ background:{button_hover};border-color:{accent}; }}
            QPushButton:pressed {{ background:{button_hover};border:2px solid {accent}; }}
            QPushButton[swatch="true"] {{ background:{field};border:1px solid {control_border}; }}
            QPushButton[swatch="true"]:hover {{ border:1px solid {accent};background:{button_hover}; }}
            QPushButton#primary {{ background:#3e72e4;color:white;border:0;font-weight:600;padding:10px; }}
            QComboBox,QLineEdit,QDoubleSpinBox,QPlainTextEdit {{ background:{field};border:1px solid {control_border};border-radius:8px;padding:6px; }}
            QComboBox:focus,QLineEdit:focus,QDoubleSpinBox:focus,QPlainTextEdit:focus {{ border:2px solid {accent}; }}
            QPushButton#primary:hover {{ background:#2d60d2; }}
            QPushButton#primary:pressed {{ background:#234eae; }}
            QComboBox::down-arrow {{ image:url("{arrow}");width:12px;height:8px; }}
            QComboBox::drop-down {{ width:24px;border-left:1px solid {control_border}; }}
            QComboBox QAbstractItemView {{ background:{'#263349' if dark else '#ffffff'};color:{fg};selection-background-color:#3569dc; }}
            QTabWidget::pane {{ border:0;background:transparent; }}
            QTabBar::tab {{ padding:8px 12px;color:{muted};border-bottom:2px solid transparent; }}
            QTabBar::tab:selected {{ color:{accent};border-bottom:2px solid {accent}; }}
            QScrollArea {{ border:0;background:transparent; }}
            QScrollArea>QWidget>QWidget {{ background:transparent; }}
            QSlider::groove:horizontal {{ height:4px;background:{'#435168' if dark else '#d5dfee'};border-radius:2px; }}
            QSlider::sub-page:horizontal {{ background:#8bacf2;border-radius:2px; }}
            QSlider::handle:horizontal {{ width:14px;margin:-5px 0;border-radius:7px;background:#5785e8; }}
            QCheckBox {{ spacing:7px;padding:3px 0; }}
            QCheckBox::indicator {{ width:15px;height:15px; }}
            QSplitter::handle {{ background:transparent;width:12px; }}
            QListWidget {{ background:{field};border:1px solid {border};border-radius:10px;padding:5px; }}
            QListWidget::item {{ padding:8px;border-radius:8px; }}
            QListWidget::item:selected {{ background:{'#355175' if dark else '#dae6fb'}; }}
            QToolTip {{ background:#243c60;color:white;border:0;padding:6px; }}
        ''')
        if hasattr(self,'mode_switch'):
            self.mode_switch.blockSignals(True);self.mode_switch.setCurrentIndex(self.mode_switch.findData(mode));self.mode_switch.blockSignals(False)
        self.update()
        if hasattr(self,'previews'):self.refresh()
        if persist:
            root=self.local_root();root.mkdir(parents=True,exist_ok=True);(root/'preferences.json').write_text(json.dumps({'mode':mode}))
    def fit_previews(self):
        for label,pix in zip(self.previews,self.preview_pixmaps):label.set_source(pix)
    def resizeEvent(self,event):
        super().resizeEvent(event)
        if hasattr(self,'preview_pixmaps'):self.fit_previews()
    def local_root(self):
        data=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
        return data/'fcitx5-theme-studio'
    def restore_session(self):
        root=self.local_root()
        try:
            preferences=root/'preferences.json'
            if preferences.exists():self.set_mode(json.loads(preferences.read_text()).get('mode','day'),persist=False)
            if (root/'last-session.json').exists():self.load_design(root/'last-session.json');self.status.setText('已恢复上次编辑 · 作品与主题都在本地')
        except (OSError,ValueError,TypeError):self.status.setText('上次设计未能载入，可以手动打开已保存的设计。')
    def closeEvent(self,event):
        try:
            root=self.local_root();root.mkdir(parents=True,exist_ok=True);self.save_design(root/'last-session.json')
        except (OSError,ValueError) as e:
            answer=QMessageBox.question(self,'保存未完成',f'无法保存上次编辑：{e}\n是否仍然关闭？',QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
            if answer!=QMessageBox.StandardButton.Yes:event.ignore();return
        event.accept()
    def build_library(self,tabs):
        body=QWidget();layout=QVBoxLayout(body);layout.setContentsMargins(12,14,12,14);layout.setSpacing(10)
        hint=QLabel('我的本地作品\n关闭时自动保存编辑进度，命名作品可以随时重新打开。');hint.setObjectName('muted');hint.setWordWrap(True);layout.addWidget(hint)
        self.work_title=QLineEdit();self.work_title.setPlaceholderText('作品名称');self.work_title.setMaxLength(80);layout.addWidget(self.work_title)
        self.work_description=QPlainTextEdit();self.work_description.setPlaceholderText('备注（可选）');self.work_description.setMaximumHeight(70);layout.addWidget(self.work_description)
        self.button(layout,'保存当前设计到作品库',self.save_work,'primary')
        self.works=QListWidget();self.works.setMinimumHeight(120);self.works.setIconSize(QSize(100,48));self.works.currentItemChanged.connect(self.select_work);layout.addWidget(self.works,1)
        self.button(layout,'打开选中的作品',self.open_work)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setWidget(body);tabs.addTab(scroll,'作品库');return layout
    def refresh_library(self):
        from library_store import read_meta
        self.works.clear();root=self.local_root()/'library'
        if not root.exists():return
        for folder in sorted(root.iterdir(),reverse=True):
            if not folder.is_dir():continue
            try:meta=read_meta(folder)
            except (OSError,ValueError,TypeError):continue
            item=QListWidgetItem(meta['title']);item.setData(Qt.ItemDataRole.UserRole,str(folder))
            if (folder/'preview.png').exists():item.setIcon(QIcon(str(folder/'preview.png')))
            self.works.addItem(item)
    def selected_folder(self):
        item=self.works.currentItem();return Path(item.data(Qt.ItemDataRole.UserRole)) if item else None
    def select_work(self,item,previous=None):
        if not item:return
        from library_store import read_meta
        meta=read_meta(Path(item.data(Qt.ItemDataRole.UserRole)));self.work_title.setText(meta['title']);self.work_description.setPlainText(meta['description'])
    def save_work(self):
        from library_store import metadata
        import uuid
        folder=self.local_root()/'library'/uuid.uuid4().hex;folder.mkdir(parents=True)
        self.save_design(folder/'design.json');meta=metadata(self.work_title.text(),self.work_description.toPlainText())
        (folder/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));self.render_preview(480,90).scaledToWidth(280,Qt.TransformationMode.SmoothTransformation).save(str(folder/'preview.png'))
        self.refresh_library();self.status.setText('已保存到本地作品库，设计和图片都已保留。')
        return folder
    def open_work(self):
        folder=self.selected_folder()
        if not folder:self.status.setText('请先选择一个作品。');return
        self.load_design(folder/'design.json');self.status.setText('作品已打开；点击应用按钮才会更改输入法主题。')
    def look_preset(self,name):
        styles={
            'sky':dict(bg='#e2efff',fg='#182635',accent='#4084c8',selected_fg='#ffffff',opacity=95),
            'night':dict(bg='#141b2a',fg='#e1e9f8',accent='#638aef',selected_fg='#ffffff',opacity=100),
            'paper':dict(bg='#fffaf2',fg='#3d352e',accent='#c98862',selected_fg='#ffffff',opacity=100)}
        self.s.update(styles[name]);self.refresh()
    def choose_placement(self,value):
        if value=='wallpaper':
            self.s['separate_candidates']=False;self.preset('cover','Center')
        else:
            self.s['separate_candidates']=True;self.preset('contain','TopLeft' if value=='left' else 'TopRight')
    def align_picture(self):
        self.preset(self.s['image_mode'],self.s['anchor'])
    def button(self,row,title,fn,kind=None):
        b=QPushButton(title)
        if kind:b.setObjectName(kind)
        b.clicked.connect(lambda _:self.safe(fn));row.addWidget(b);return b
    def safe(self,fn):
        try:fn()
        except Exception as e:QMessageBox.warning(self,'操作未完成',str(e))
    def change(self,k,v):
        if k=='zoom' and self.picture and not self.picture.isNull():
            old=image_rect(self.s,self.picture,self.s['image_width'],self.s['image_height'])
            self.s[k]=v
            new=image_rect(self.s,self.picture,self.s['image_width'],self.s['image_height'])
            self.s['image_dx']+=old.center().x()-new.center().x()
            self.s['image_dy']+=old.center().y()-new.center().y()
        elif k in ('pan_x','pan_y'):
            # Alignment controls must override any accumulated drag/zoom offset.
            self.s[k]=v;self.s['image_dx' if k=='pan_x' else 'image_dy']=0.0
        else:self.s[k]=v
        self.refresh()
    def color(self,k):
        c=QColorDialog.getColor(QColor(self.s[k]),self)
        if c.isValid():self.s[k]=c.name();self.refresh()
    def separate_picture(self):
        self.s.update(separate_candidates=True,background_style='stable',anchor='TopRight',picture_space=max(160,self.s['picture_space']))
        self.refresh()
    def refresh(self):
        if self.s['separate_candidates'] and self.s['anchor']=='Center':self.s['anchor']='TopRight'
        self.image_name.setText(Path(self.picture_path).name if self.picture_path else '尚未选择图片 · 推荐透明 PNG')
        value='left' if self.s['anchor']=='TopLeft' else 'right' if self.s['separate_candidates'] else 'wallpaper'
        self.placement.blockSignals(True);self.placement.setCurrentIndex(self.placement.findData(value));self.placement.blockSignals(False)
        self.spacing.setEnabled(self.s['separate_candidates'] and self.s['background_style']=='stable')
        self.spacing.blockSignals(True);self.spacing.setValue(self.s['picture_space']);self.spacing.blockSignals(False)
        for key,spin in self.offsets.items():
            spin.blockSignals(True);spin.setValue(self.s[key]);spin.blockSignals(False)
        for k,b in self.colors.items():
            chip=QPixmap(26,26);chip.fill(Qt.GlobalColor.transparent);p=QPainter(chip);p.setRenderHint(QPainter.RenderHint.Antialiasing);p.setBrush(QColor(self.s[k]));p.setPen(QPen(QColor('#8195b3'),1));p.drawRoundedRect(QRectF(2,2,22,22),5,5);p.end()
            b.setIcon(QIcon(chip));b.setIconSize(QSize(26,26));b.setText(self.s[k]+' · 选色')
        for k,(slider,label,title) in self.sliders.items():slider.blockSignals(True);slider.setValue(self.s[k]);slider.blockSignals(False);label.setText(f'{title}：{self.s[k]}')
        self.highlight.blockSignals(True);self.highlight.setChecked(self.s['highlight']);self.highlight.blockSignals(False)
        self.mode.blockSignals(True);self.mode.setCurrentIndex(self.mode.findData(self.s['image_mode']));self.mode.blockSignals(False)
        for checkbox,key in [(self.fit,'fit_candidate_height'),(self.preedit,'preview_preedit'),(self.edge,'edge_fill'),(self.separate,'separate_candidates')]:
            checkbox.blockSignals(True);checkbox.setChecked(self.s[key]);checkbox.blockSignals(False)
        for combo,key in [(self.style,'background_style'),(self.anchor,'anchor')]:
            combo.blockSignals(True);combo.setCurrentIndex(combo.findData(self.s[key]));combo.blockSignals(False)
        self.editor.update()
        self.preview_pixmaps=[self.render_preview(width,self.s['preview_height']) for width in (220,self.s['preview_width'],600)]
        self.fit_previews()
    def preset(self,mode,anchor):
        self.s.update(image_mode=mode,anchor=anchor,zoom=100,image_dx=0.0,image_dy=0.0,pan_x=100 if anchor=='TopRight' else 0 if anchor=='TopLeft' else 50,pan_y=50,background_style='stable',fit_candidate_height=True);self.refresh()
    def render_preview(self,w,h):
        left,right=content_margins(self.s,bool(self.picture));margin=max(8,self.s['radius'])
        w+=left+right-2*margin
        pix=QPixmap(w+30,h+30);pix.fill(QColor('#263349' if self.ui_mode=='night' else '#edf2f9'));p=QPainter(pix);p.translate(15,15)
        p.drawPixmap(0,0,theme_preview(self.s,self.picture,w,h));p.setClipRect(left,0,max(0,w-left-right),h)
        font=p.font();font.setPointSize(self.s['size']);p.setFont(font);metrics=p.fontMetrics();gap=self.s['gap'];margin=max(8,self.s['radius']);y=margin+metrics.ascent();p.setPen(QColor(self.s['fg']));
        if self.s['preview_preedit']:p.drawText(left,y,'ni hao')
        baseline=y+(metrics.height()+2*gap if self.s['preview_preedit'] else gap);x=left
        count=2 if w-left-right+2*margin<=250 else 4 if w-left-right+2*margin<=500 else 6
        for i,text in enumerate(['1 你好','2 世界','3 主题','4 自由','5 设计','6 简单'][:count]):
            width=metrics.horizontalAdvance(text)+2*gap
            if i==0:p.fillRect(x,baseline-metrics.ascent()-gap,width,metrics.height()+2*gap,self.preview_highlight())
            p.setPen(QColor(self.s['selected_fg'] if i==0 else self.s['fg']));p.drawText(x+gap,baseline,text);x+=width
        p.end();return pix
    def preview_highlight(self):
        c=QColor(self.s['accent']);c.setAlpha(round(255*self.s['highlight_opacity']/100) if self.s['highlight'] else 0);return c
    def image(self):
        path,_=QFileDialog.getOpenFileName(self,'选择图片','','图片 (*.png *.jpg *.jpeg *.webp)')
        if path:self.read_image(path);self.refresh()
    def read_image(self,path):
        if Path(path).stat().st_size>10*1024*1024:raise ValueError('图片不能超过 10MB')
        pix=QPixmap(path)
        if pix.isNull():raise ValueError('无法读取图片')
        self.picture=pix;self.picture_path=path;self.s.update(image_dx=0.0,image_dy=0.0)
    def clear(self):self.picture=None;self.picture_path='';self.refresh()
    def reset(self):self.s=DEFAULT.copy();self.clear()
    def save(self):
        path,_=QFileDialog.getSaveFileName(self,'保存设计','design.json','JSON (*.json)')
        if path:self.save_design(Path(path));self.status.setText('设计已保存。分享时发送 JSON 与同名素材文件夹。')
    def save_design(self,path):
        path=Path(path)
        if path.suffix.lower()!='.json':path=path.with_suffix('.json')
        image=''
        if self.picture and not self.picture.isNull():
            assets=path.with_name(path.stem+'.assets');assets.mkdir(parents=True,exist_ok=True)
            target=assets/'image.png'
            if not self.picture.save(str(target)):raise OSError('无法保存设计图片')
            image=target.relative_to(path.parent).as_posix()
        path.write_text(json.dumps(dict(version=2,settings=self.s,image=image),ensure_ascii=False,indent=2))
        return path
    def load(self):
        path,_=QFileDialog.getOpenFileName(self,'载入设计','','JSON (*.json)')
        if path:self.load_design(Path(path))
    def load_design(self,path):
        path=Path(path);d=json.loads(path.read_text())
        if not isinstance(d,dict) or d.get('version') not in (1,2) or not isinstance(d.get('settings'),dict):raise ValueError('不支持此设计文件')
        s={**DEFAULT,**d['settings']}
        for k in self.colors:
            if not isinstance(s.get(k),str) or not re.fullmatch('#[0-9a-fA-F]{6}',s[k]):raise ValueError('颜色无效')
        for k,(slider,_,_) in self.sliders.items():
            if type(s.get(k)) is not int or not slider.minimum()<=s[k]<=slider.maximum():raise ValueError('尺寸无效')
        if s.get('image_mode') not in ('cover','contain','stretch') or s['background_style'] not in ('stable','rounded') or s['anchor'] not in ('TopRight','TopLeft','Center'):raise ValueError('图片布局无效')
        if any(type(s[k]) is not bool for k in ('highlight','fit_candidate_height','preview_preedit','edge_fill','separate_candidates')):raise ValueError('设计选项无效')
        if type(s['picture_space']) is not int or not 0<=s['picture_space']<=600:raise ValueError('人物区域宽度无效')
        for key in ('image_dx','image_dy'):
            if type(s[key]) not in (int,float) or not -100000<=s[key]<=100000:raise ValueError('图片偏移无效')
        image=d.get('image','')
        if not isinstance(image,str):raise ValueError('图片路径无效')
        target=Path(image) if image else None
        if target and d['version']==2:
            target=(path.parent/target).resolve()
            if not target.is_relative_to(path.parent.resolve()):raise ValueError('设计图片必须位于设计文件夹内')
        elif target and not target.is_absolute():target=path.parent/target
        picture=None
        if target and target.is_file():
            if target.stat().st_size>10*1024*1024:raise ValueError('图片不能超过 10MB')
            picture=QPixmap(str(target))
            if picture.isNull():raise ValueError('无法读取设计图片')
        self.s={k:s[k] for k in DEFAULT};self.picture=picture;self.picture_path=str(target) if picture else ''
        self.refresh();self.status.setText('设计已载入' if not image or picture else '设计已载入，但素材缺失；请重新导入图片。')
    def write_theme(self,dest):
        dest.mkdir(parents=True,exist_ok=True);(dest/'theme.conf').write_text(config_text(self.s,bool(self.picture)))
        if not background(self.s,self.picture if self.s['background_style']=='rounded' else None,self.s['image_width'],self.s['image_height']).save(str(dest/'background.png')):raise OSError('背景图片保存失败')
        if not image_layer(self.s,self.picture).save(str(dest/'picture.png')):raise OSError('背景图片保存失败')
    def export(self):
        path=QFileDialog.getExistingDirectory(self,'选择导出父目录')
        if path:self.write_theme(Path(path)/'theme-studio');self.status.setText('主题已导出至 '+str(Path(path)/'theme-studio'))
    def paths(self):
        config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'fcitx5/conf/classicui.conf'
        data=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))
        return config,data/'fcitx5/themes/theme-studio',data/'fcitx5-theme-studio/backups'
    def reload(self):
        try:
            r=subprocess.run(['gdbus','call','--session','--dest','org.fcitx.Fcitx5','--object-path','/controller','--method','org.fcitx.Fcitx.Controller1.ReloadAddonConfig','classicui'],capture_output=True,text=True,timeout=5)
            return '已通知 Fcitx5 重载。' if r.returncode==0 else '配置已保存，但重载失败；请在经典界面设置中确认主题。'
        except (OSError,subprocess.TimeoutExpired):return '配置已保存；请在经典界面设置中确认主题。'
    def apply(self):
        config,theme,backups=self.paths();stamp=datetime.now().strftime('%Y%m%d-%H%M%S-%f');backup=backups/stamp;backup.mkdir(parents=True)
        (backup/'existed').write_text('yes' if config.exists() else 'no')
        if config.exists():shutil.copy2(config,backup/'classicui.conf')
        (backup/'theme-existed').write_text('yes' if theme.exists() else 'no')
        if theme.exists():shutil.copytree(theme,backup/'theme')
        self.write_theme(theme);text=config.read_text() if config.exists() else ''
        for key,value in [('Theme','theme-studio'),('DarkTheme','theme-studio'),('UseDarkTheme','False'),('UseAccentColor','False'),('Font',f'Sans {self.s["size"]}')]:
            pattern=r'^'+key+r'=.*$'
            text=re.sub(pattern,key+'='+value,text,flags=re.M) if re.search(pattern,text,re.M) else key+'='+value+'\n'+text
        config.parent.mkdir(parents=True,exist_ok=True);temp=config.with_suffix('.tmp');temp.write_text(text);temp.replace(config)
        self.status.setText(self.reload()+' 备份：'+str(backup))
    def restore(self):
        config,theme,backups=self.paths();items=sorted(backups.iterdir()) if backups.exists() else []
        if not items:raise ValueError('没有可恢复的备份')
        backup=items[-1]
        if (backup/'existed').read_text()=='yes':
            config.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(backup/'classicui.conf',config)
        elif config.exists():config.unlink()
        if (backup/'theme').exists():
            if theme.exists():shutil.rmtree(theme)
            shutil.copytree(backup/'theme',theme)
        elif (backup/'theme-existed').exists() and (backup/'theme-existed').read_text()=='no' and theme.exists():shutil.rmtree(theme)
        self.status.setText('已恢复最近一次应用前的配置。'+self.reload())

def main():
    if '--version' in sys.argv:print('Fcitx5 Theme Studio 0.3.1');sys.exit(0)
    app=QApplication(sys.argv);app.setApplicationName('Fcitx5 Theme Studio');app.setStyle('Fusion');window=Studio();window.show();sys.exit(app.exec())


if __name__=='__main__':main()
