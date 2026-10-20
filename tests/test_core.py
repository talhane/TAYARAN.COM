import sys, unittest, tempfile, os
from pathlib import Path
from datetime import date, datetime
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from ea.content import LESSONS, EXERCISES
from ea.wing3d import build_wing, wing_estimates, stl_bytes
from ea.storage import defaults, save_progress, load_progress, export_progress
from ea import auth
class CoreTests(unittest.TestCase):
 def test_course_counts(self):
  self.assertEqual(len(LESSONS),15); self.assertEqual(len(EXERCISES),60)
  self.assertEqual(sum(x['subject']=='mech' for x in LESSONS),5)
  self.assertEqual(sum(x['subject']=='fluid' for x in LESSONS),5)
  self.assertEqual(sum(x['subject']=='aero' for x in LESSONS),5)
 def test_exercise_answers_finite(self): self.assertTrue(all(abs(x['answer'])<1e12 for x in EXERCISES))
 def test_wing_mesh_and_stl(self):
  X,Y,Z=build_wing('0012',2,1,nx=10,ny=6); self.assertEqual(X.shape,Y.shape); self.assertEqual(X.shape,Z.shape); self.assertTrue(stl_bytes(X,Y,Z).startswith(b'Engineering'))
 def test_estimates(self): self.assertIn('Lift (N)',wing_estimates(4,1,30,4,1.225,'0012'))
 def test_defaults(self): self.assertEqual(defaults()['completed_lessons'],[])
 def test_auth_register_login_change_password_and_consents(self):
  with tempfile.TemporaryDirectory() as td:
   os.environ['EA_DATA_DIR']=td
   try:
    ok, role = auth.register('khalid@example.com','SecurePass123','Khalid Talhane',True)
    self.assertTrue(ok); self.assertEqual(role,'admin')
    user = auth.authenticate('KHALID@example.com','SecurePass123')
    self.assertEqual(user['role'],'admin')
    ok, role = auth.register('student@example.com','StudentPass123','Student',True)
    self.assertTrue(ok); self.assertEqual(role,'student')
    self.assertIsNone(auth.authenticate('student@example.com','wrongpass'))
    changed, _ = auth.change_password('student@example.com','StudentPass123','NewSecure456')
    self.assertTrue(changed); self.assertIsNotNone(auth.authenticate('student@example.com','NewSecure456'))
    auth.update_consents('student@example.com', {'study_progress':True,'uploaded_files':False,'location':True,'device_sharing':False})
    record = auth.account_record('student@example.com')
    self.assertTrue(record['consents']['location']); self.assertFalse(record['consents']['device_sharing'])
   finally: os.environ.pop('EA_DATA_DIR',None)
 def test_progress_isolated_by_user(self):
  with tempfile.TemporaryDirectory() as td:
   os.environ['EA_DATA_DIR']=td
   try:
    save_progress({'completed_lessons':[1]}, 'student-a')
    save_progress({'completed_lessons':[1,2]}, 'student-b')
    self.assertEqual(load_progress('student-a')['completed_lessons'],[1])
    self.assertEqual(load_progress('student-b')['completed_lessons'],[1,2])
   finally: os.environ.pop('EA_DATA_DIR',None)
 def test_date_values_are_json_serializable(self):
  payload=defaults(); payload['personal_life']={'annual_start':date(2026,10,18),'saved_at':datetime(2026,10,18,12,30)}
  raw=export_progress(payload).decode('utf-8')
  self.assertIn('2026-10-18',raw); self.assertIn('2026-10-18T12:30:00',raw)
  with tempfile.TemporaryDirectory() as td:
   os.environ['EA_DATA_DIR']=td
   try:
    save_progress(payload); loaded=load_progress(); self.assertEqual(loaded['personal_life']['annual_start'],'2026-10-18')
   finally: os.environ.pop('EA_DATA_DIR',None)
if __name__=='__main__': unittest.main()
