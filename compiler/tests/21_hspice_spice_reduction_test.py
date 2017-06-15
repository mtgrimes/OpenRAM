#!/usr/bin/env python2.7
"""
Run a regresion test on various srams
"""

import unittest
from testutils import header,isclose
import sys,os
sys.path.append(os.path.join(sys.path[0],".."))
import globals
import debug
import calibre

OPTS = globals.get_opts()

class timing_sram_test(unittest.TestCase):

    def runTest(self):
        globals.init_openram("config_20_{0}".format(OPTS.tech_name))
        # we will manually run lvs/drc
        OPTS.check_lvsdrc = False
        OPTS.spice_version="hspice"
        OPTS.force_spice = True
	#OPTS.trim_noncritical = True
        globals.set_spice()
        
        import sram

        debug.info(1, "Testing timing for sample 2bits, 16words SRAM with 1 bank")
        s = sram.sram(word_size=2,#OPTS.config.word_size,
                      num_words=16,#OPTS.config.num_words,
                      num_banks=1,#OPTS.config.num_banks,
                      name="test_sram1")

        OPTS.check_lvsdrc = True

        import delay

        tempspice = OPTS.openram_temp + "temp.sp"
        s.sp_write(tempspice)

        probe_address = "1" * s.addr_size
        probe_data = s.word_size - 1
        debug.info(1, "Probe address {0} probe data {1}".format(probe_address, probe_data))

        d = delay.delay(s,tempspice)
        d.reduction_mode("full")
        data = d.analyze(probe_address, probe_data)
		
        r = delay.delay(s,tempspice)
        r.reduction_mode("reduce")
        rdata = r.analyze(probe_address, probe_data)

        print "delay1:\n  full {}\n  reduced {}".format(data['delay1'],rdata['delay1'])
        print "delay0:\n  full {}\n  reduced {}".format(data['delay0'],rdata['delay0'])
        print "min_period1:\n  full {}\n  reduced {}".format(data['min_period1'],rdata['min_period1'])
        print "min_period0:\n  full {}\n  reduced {}".format(data['min_period0'],rdata['min_period0'])

        if OPTS.tech_name == "freepdk45":
            self.assertTrue(isclose(data['delay1'],rdata['delay1']))
            self.assertTrue(isclose(data['delay0'],rdata['delay0']))
            self.assertTrue(isclose(data['min_period1'],rdata['min_period1']))
            self.assertTrue(isclose(data['min_period0'],rdata['min_period0']))
        elif OPTS.tech_name == "scn3me_subm":
            self.assertTrue(isclose(data['delay1'],rdata['delay1']))
            self.assertTrue(isclose(data['delay0'],rdata['delay0']))
            self.assertTrue(isclose(data['min_period1'],rdata['min_period1']))
            self.assertTrue(isclose(data['min_period0'],rdata['min_period0']))
        else:
            self.assertTrue(False) # other techs fail

        os.remove(tempspice)

        globals.end_openram()
        
# instantiate a copdsay of the class to actually run the test
if __name__ == "__main__":
    (OPTS, args) = globals.parse_args()
    del sys.argv[1:]
    header(__file__, OPTS.tech_name)
    unittest.main()
