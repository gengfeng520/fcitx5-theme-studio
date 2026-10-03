"""Behavior checks; all application writes are isolated in temporary XDG dirs."""
import os,sys,json,shutil,tempfile,unittest,configparser
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import studio as m

class StudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=m.QApplication.instance() or m.QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.env=patch.dict(os.environ,{'XDG_CONFIG_HOME':str(self.root/'config'),'XDG_DATA_HOME':str(self.root/'data')});self.env.start()
        self.w=m.Studio();self.w.reload=lambda:'test reload'
    def tearDown(self):
        self.w.close();self.env.stop();self.temp.cleanup()
    def picture(self):
        self.w.picture=m.QPixmap(100,180);self.w.picture.fill(m.QColor('red'))
    def test_zoom_keeps_center_and_proportions(self):
        self.picture();self.w.s.update(image_mode='contain',pan_x=0,image_dx=47,image_dy=-8)
        old=m.image_rect(self.w.s,self.w.picture,580,150);self.w.change('zoom',175)
        new=m.image_rect(self.w.s,self.w.picture,580,150)
        self.assertEqual(old.center(),new.center());self.assertAlmostEqual(new.width()/old.width(),1.75);self.assertAlmostEqual(new.height()/old.height(),1.75)
    def test_separation_survives_preset_width_changes(self):
        self.picture();self.w.spacing.setValue(192);self.w.preset('contain','Center')
        for width in (220,480,600):
            self.w.change('image_width',width);self.w.change('preview_width',width)
            c=configparser.ConfigParser();c.read_string(m.config_text(self.w.s,True))
            self.assertEqual(c['InputPanel/Background']['Gravity'],'Top Right');self.assertEqual(c['InputPanel/ContentMargin']['Right'],'210')
        self.w.choose_placement('left');c=configparser.ConfigParser();c.read_string(m.config_text(self.w.s,True))
        self.assertEqual(c['InputPanel/Background']['Gravity'],'Top Left');self.assertEqual(c['InputPanel/ContentMargin']['Left'],'210')
    def test_image_edges_match_background(self):
        self.picture();self.w.s.update(image_mode='contain',pan_x=100,opacity=100)
        for height in (70,90,110):
            out=m.background(self.w.s,self.w.picture,480,height).toImage()
            self.assertEqual(out.pixelColor(450,0).alpha(),0);self.assertEqual(out.pixelColor(450,height-1).alpha(),0)
            self.assertGreater(out.pixelColor(450,1).red(),240);self.assertGreater(out.pixelColor(450,height-2).red(),240)
    def test_portable_design_survives_move(self):
        self.picture();self.w.s.update(image_dx=37.5,zoom=125)
        original=self.root/'original';original.mkdir();self.w.save_design(original/'design.json')
        moved=self.root/'moved';shutil.copytree(original,moved);shutil.rmtree(original)
        self.w.clear();self.w.load_design(moved/'design.json')
        self.assertEqual(self.w.picture.size(),m.QPixmap(str(moved/'design.assets/image.png')).size());self.assertEqual(self.w.s['image_dx'],37.5);self.assertEqual(self.w.s['zoom'],125)
    def test_legacy_design_and_validation(self):
        self.picture();picture=self.root/'legacy.png';self.w.picture.save(str(picture))
        path=self.root/'old.json';path.write_text(json.dumps({'version':1,'settings':{'zoom':130},'image':str(picture)}))
        self.w.load_design(path);self.assertEqual(self.w.s['zoom'],130)
        before=self.w.s.copy();path.write_text(json.dumps({'version':2,'settings':{'image_dx':float('nan')},'image':''}))
        with self.assertRaises(ValueError):self.w.load_design(path)
        self.assertEqual(self.w.s,before)
        path.write_text(json.dumps({'version':2,'settings':{},'image':'../outside.png'}))
        with self.assertRaises(ValueError):self.w.load_design(path)
    def test_export_has_files_and_correct_geometry(self):
        self.picture();self.w.write_theme(self.root/'theme')
        self.assertEqual({p.name for p in (self.root/'theme').iterdir()},{'theme.conf','background.png','picture.png'})
        c=configparser.ConfigParser();c.read(self.root/'theme/theme.conf')
        self.assertEqual(c['InputPanel/Background/OverlayClipMargin']['Top'],'1')
        self.assertEqual(c['InputPanel/ContentMargin']['Right'],'178')
    def test_apply_restore_existing_theme(self):
        config,theme,_=self.w.paths();config.parent.mkdir(parents=True);config.write_text('Theme=original\nFont=Sans 12\n')
        theme.mkdir(parents=True);(theme/'original.txt').write_text('keep me')
        self.w.apply();self.assertIn('Theme=theme-studio',config.read_text());self.w.restore()
        self.assertEqual(config.read_text(),'Theme=original\nFont=Sans 12\n');self.assertEqual((theme/'original.txt').read_text(),'keep me')
    def test_apply_restore_initially_absent_theme(self):
        config,theme,_=self.w.paths();self.w.apply();self.assertTrue(theme.is_dir());self.w.restore()
        self.assertFalse(config.exists());self.assertFalse(theme.exists())
    def test_presets_do_not_discard_imported_picture(self):
        self.picture();before=self.w.picture.cacheKey();self.w.look_preset('night')
        self.assertEqual(self.w.picture.cacheKey(),before);self.assertEqual(self.w.s['bg'],'#141b2a')
        self.w.choose_placement('right');self.assertTrue(self.w.s['separate_candidates']);self.assertEqual(self.w.s['pan_x'],100)
        self.w.choose_placement('wallpaper');self.assertFalse(self.w.s['separate_candidates'])

if __name__=='__main__':unittest.main()
