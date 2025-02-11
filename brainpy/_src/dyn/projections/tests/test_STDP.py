# -*- coding: utf-8 -*-


from absl.testing import parameterized

import brainpy as bp
import brainpy.math as bm

class Test_STDP(parameterized.TestCase):
  def test_STDP(self):
    bm.random.seed()
    class STDPNet(bp.DynamicalSystem):
      def __init__(self, num_pre, num_post):
        super().__init__()
        self.pre = bp.dyn.LifRef(num_pre, name='neu1')
        self.post = bp.dyn.LifRef(num_post, name='neu2')
        self.syn = bp.dyn.STDP_Song2000(
          pre=self.pre,
          delay=1.,
          comm=bp.dnn.EventCSRLinear(bp.conn.FixedProb(1, pre=self.pre.num, post=self.post.num),
                                     weight=lambda s: bm.Variable(bm.random.rand(*s) * 0.1)),
          syn=bp.dyn.Expon.desc(self.post.varshape, tau=5.),
          out=bp.dyn.COBA.desc(E=0.),
          post=self.post,
          tau_s=16.8,
          tau_t=33.7,
          A1=0.96,
          A2=0.53,
        )

      def update(self, I_pre, I_post):
        self.syn()
        self.pre(I_pre)
        self.post(I_post)
        conductance = self.syn.refs['syn'].g
        Apre = self.syn.refs['pre_trace'].g
        Apost = self.syn.refs['post_trace'].g
        current = self.post.sum_inputs(self.post.V)
        return self.pre.spike, self.post.spike, conductance, Apre, Apost, current, self.syn.comm.weight

    duration = 300.
    I_pre = bp.inputs.section_input([0, 30, 0, 30, 0, 30, 0, 30, 0, 30, 0, 30, 0],
                                    [5, 15, 15, 15, 15, 15, 100, 15, 15, 15, 15, 15, duration - 255])
    I_post = bp.inputs.section_input([0, 30, 0, 30, 0, 30, 0, 30, 0, 30, 0, 30, 0],
                                     [10, 15, 15, 15, 15, 15, 90, 15, 15, 15, 15, 15, duration - 250])

    net = STDPNet(1, 1)
    def run(i, I_pre, I_post):
      pre_spike, post_spike, g, Apre, Apost, current, W = net.step_run(i, I_pre, I_post)
      return pre_spike, post_spike, g, Apre, Apost, current, W

    indices = bm.arange(0, duration, bm.dt)
    bm.for_loop(run, [indices, I_pre, I_post], jit=True)
    bm.clear_buffer_memory()