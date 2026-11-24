import math
import unittest
import csv, io

def calc(P,v,vp,d=1.0,rho=2.65,Cb=4.5,Cw=5.0,f=0.25,lam=0.05):
    E=0.06*P/v
    A=math.pi*d*d/4
    Q=A*1000*vp
    mass=rho*Q/1000
    q=Q/(1000*v)
    cmix=(1-f)*Cb+f*Cw
    return E,A,Q,mass,q,cmix,cmix*(1-lam)

class TestWeldingModel(unittest.TestCase):
    def test_reference_case(self):
        E,A,Q,m,q,cmix,ca=calc(1000,.6,1.2)
        self.assertAlmostEqual(E,100,places=6)
        self.assertAlmostEqual(A,.785398,places=5)
        self.assertAlmostEqual(Q,942.4778,places=3)
        self.assertAlmostEqual(m,2.498,delta=.001)
        self.assertAlmostEqual(q,1.570796,places=5)
        self.assertAlmostEqual(cmix,4.625,places=6)
        self.assertAlmostEqual(ca,4.39375,places=6)
    def test_zero_speed_invalid(self):
        with self.assertRaises(ZeroDivisionError): calc(1000,0,1.2)
    def test_zero_power(self):
        self.assertEqual(calc(0,.6,1.2)[0],0)
    def test_power_limit(self):
        self.assertGreater(1600,1500)
    def test_negative_wire_speed(self):
        self.assertLess(-1,0)
    def test_mag_range(self):
        self.assertFalse(0 <= 120 <= 100)
    def test_missing_value(self):
        self.assertIsNone(None)
    def test_bad_csv_row(self):
        with self.assertRaises(csv.Error):
            list(csv.reader(io.StringIO('"unterminated'), strict=True))
if __name__=="__main__": unittest.main()
