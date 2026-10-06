"""Numerical provenance, aligned rows, and delivery-size text bounds for M8."""
from pathlib import Path
import sys
import unittest
import warnings
from unittest.mock import patch
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'visualization-curriculum'))
import evidence_tables as et


class EvidenceTables(unittest.TestCase):
    def tearDown(self):
        plt.close('all')

    def test_historical_sleep_pairing(self):
        self.assertAlmostEqual(et.SLEEP_1.mean(),.75)
        self.assertAlmostEqual(et.SLEEP_2.mean(),2.33)
        np.testing.assert_allclose(et.mean_ci10(et.SLEEP_2-et.SLEEP_1),
                                   [1.58,.7001142367,2.4598857633],atol=1e-10)
        with self.assertRaises(ValueError):
            et.mean_ci10([1,2,3])

    def test_berkeley_denominators(self):
        counts,mn,fn,mr,fr=et.berkeley_records()
        self.assertEqual(int(et.BERKELEY.sum()),4526)
        self.assertEqual((int(mn[0]),int(fn[0])),(2691,1835))
        self.assertEqual((int(counts[0,0]),int(counts[0,2])),(1198,557))
        np.testing.assert_allclose(mr,100*counts[:,0]/mn)
        np.testing.assert_allclose(fr,100*counts[:,2]/fn)

    def test_bootstrap_reproducibility_and_contrast(self):
        rows,interval=et.synthetic_trials()
        other,other_interval=et.synthetic_trials()
        np.testing.assert_array_equal(interval,other_interval)
        np.testing.assert_allclose([r['effect'] for r in rows],[6,3,1],atol=1e-12)
        np.testing.assert_allclose(interval,np.quantile(rows[0]['boot']-rows[1]['boot'],[.025,.975]))
        self.assertLess(interval[0],0)
        self.assertGreater(interval[1],0)
        for r,s in zip(rows,other):
            np.testing.assert_array_equal(r['boot'],s['boot'])
            self.assertEqual(len(r['control']),r['n'])

    def test_figures_text_bounds_and_row_alignment(self):
        builders=(et.sleep_before,et.sleep_glance,et.sleep_read,et.sleep_study,et.berkeley_figure,et.trials_figure)
        with patch.object(et,'export',side_effect=lambda fig,stem:fig):
            for build in builders:
                with self.subTest(figure=build.__name__), warnings.catch_warnings():
                    warnings.filterwarnings('error',message='Glyph.*missing.*')
                    fig=build()
                    fig.canvas.draw()
                    renderer=fig.canvas.get_renderer()
                    text=list(fig.texts)
                    for ax in fig.axes:
                        text+=list(ax.texts)+[ax.xaxis.label,ax.yaxis.label,ax.title]
                    for artist in text:
                        if not artist.get_text():
                            continue
                        box=artist.get_window_extent(renderer)
                        self.assertGreaterEqual(box.x0,-1,artist.get_text())
                        self.assertGreaterEqual(box.y0,-1,artist.get_text())
                        self.assertLessEqual(box.x1,fig.bbox.width+1,artist.get_text())
                        self.assertLessEqual(box.y1,fig.bbox.height+1,artist.get_text())
                    if len(fig.axes)==3:
                        ys=[ax.transData.transform((0,0))[1] for ax in fig.axes]
                        np.testing.assert_allclose(ys,ys[0])
                    plt.close(fig)

if __name__=='__main__':
    unittest.main()
