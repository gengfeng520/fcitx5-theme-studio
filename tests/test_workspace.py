import sys,os,tempfile,json,unittest
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import studio as m
class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=m.QApplication.instance() or m.QApplication([])
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.env=patch.dict(os.environ,{'XDG_DATA_HOME':str(self.root/'data'),'XDG_CONFIG_HOME':str(self.root/'config')});self.env.start();self.w=m.Studio()
    def tearDown(self):self.w.close();self.env.stop();self.temp.cleanup()
    def test_compact_layout_keeps_input_and_preview_visible(self):
        self.w.show();self.w.s.update(picture_space=600,preview_height=180);self.w.picture=m.QPixmap(100,180);self.w.picture.fill(m.QColor('red'));self.w.refresh()
        for width,height in [(920,640),(1120,760),(1920,1080)]:
            self.w.resize(width,height);self.app.processEvents()
            bottom=self.w.test_input.mapTo(self.w,self.w.test_input.rect().bottomRight())
            self.assertLess(bottom.y(),self.w.status.y());self.assertTrue(self.w.test_input.isVisible())
            for idx in range(3):
                self.w.preview_selector.setCurrentIndex(idx);self.app.processEvents();label=self.w.previews[idx]
                self.assertLessEqual(label.pixmap().width(),label.width());self.assertLessEqual(label.pixmap().height(),label.height())
    def test_ui_mode_does_not_change_theme_design(self):
        before=self.w.s.copy();self.w.set_mode('night');self.assertEqual(self.w.s,before)
        self.w.close();next_window=m.Studio();self.assertEqual(next_window.ui_mode,'night');next_window.close()
    def test_session_restores_picture_and_offsets(self):
        self.w.picture=m.QPixmap(100,180);self.w.picture.fill(m.QColor('red'));self.w.s.update(zoom=153,image_dx=37.5,picture_space=192);self.w.close()
        other=m.Studio();self.assertEqual(other.s['zoom'],153);self.assertEqual(other.s['image_dx'],37.5);self.assertEqual(other.s['picture_space'],192);self.assertIsNotNone(other.picture);other.close()
    def test_named_library_can_reopen_design(self):
        self.w.work_title.setText('测试作品');self.w.work_description.setPlainText('本地备注');self.w.s['bg']='#121234';folder=self.w.save_work()
        self.assertTrue((folder/'design.json').exists());self.assertEqual(json.loads((folder/'metadata.json').read_text())['title'],'测试作品')
        self.w.s['bg']='#ffffff';self.w.works.setCurrentRow(0);self.w.open_work();self.assertEqual(self.w.s['bg'],'#121234')
if __name__=='__main__':unittest.main()
