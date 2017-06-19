import globals

OPTS = globals.get_opts()

def trim(Dvar, word_size, path):
	# copy the contents of temp.sp into a new file the will afterward be reduced
	resp = "{0}reduced.sp".format(OPTS.openram_temp)
	spfile = open(path, "r")
	re_spfile = open(resp, "w")

	BCA_flag = 0	# Bit Cell Array
	PCA_flag = 0	# Precharge Array
	CMA_flag = 0	# Column Mux Array
	SAA_flag = 0	# Sense Amp Array
	WDA_flag = 0	# Write Driver Array
	DIFA_flag = 0	# Data In Flop Array
	TGA_flag = 0	# Trigate Data Array
	cell_flag = 0	# flag used for writing blank bit cell
	TBK_flag = 0	# Test Bank
	
	bit_name_flag = 0

	for line in spfile:
		if ".SUBCKT sense_amp_array" in line:
			SAA_flag = 1
		elif (".ENDS" in line) and (SAA_flag == 1):
			SAA_flag = 0			
		elif ("Xsa_d{} ".format(Dvar) in line) and (SAA_flag == 1):
			SA = line.split(" ")
			bl_out = SA[1]
			br_out = SA[2]
			data_out = SA[3]
		
		elif ".SUBCKT msf_data_in" in line:
			DIFA_flag = 1
		elif (".ENDS" in line) and (DIFA_flag == 1):
			DIFA_flag = 0
		elif ("XXdff{} ".format(Dvar) in line) and (DIFA_flag == 1):
			DIF = line.split(" ")
			DATA = DIF[1]
			data_in = DIF[2]
			data_in_bar = DIF[3]

		elif ".SUBCKT tri_gate_array" in line:
			TGA_flag = 1
		elif (".ENDS" in line) and (TGA_flag == 1):
			TGA_flag = 0
		elif ("XXtri_gate{} ".format(Dvar) in line) and (TGA_flag == 1):
			TG = line.split(" ")
			tri_in = TG[1]
			
		elif ".SUBCKT bitcell_array" in line:
			BCA_flag = 1
		elif (".ENDS" in line) and (BCA_flag == 1):
			BCA_flag = 0
		elif (".ENDS" not in line) and (BCA_flag == 1) and (bit_name_flag == 0):
			cell_line = line.split(" ")
			cell_name0 = cell_line[len(cell_line)-1].split("\n")
			cell_name = cell_name0[0]
			bit_name_flag = 1			
	spfile.seek(0)

	bl_arr = []
	br_arr = []
	Blcount = 0
	CMA_mflag = 0
	for line in spfile:
		# determining which bit lines correspond to the specified data bit
		if ".SUBCKT columnmux_array" in line:
			CMA_flag = 1
			CMA_mflag = 1
		if (".ENDS" in line) and (CMA_flag == 1):
			CMA_flag = 0			
		if ("XXMUX" in line) and (SA[1] in line) and (CMA_flag == 1):
			CM = line.split(" ")
			bl_arr.append(CM[1])
			br_arr.append(CM[2])
			Blcount += 1

		# creating a subcircuit for a blank bit cell
		if ".SUBCKT {}".format(cell_name) in line:
			cell_flag = 1
		if cell_flag == 1:
			if ".SUBCKT {}".format(cell_name) in line:
				trim_line = line.split(" ")
				blank_cell_line = []
				for i in range(0,len(trim_line)):
					if ("bl" in trim_line[i]) or ("br" in trim_line[i]):
						1 # skip
					else:
						blank_cell_line.append(trim_line[i])
				blank_cell_line[1] = "blank_cell"
				blank_cell = " ".join(blank_cell_line)
			if ("wl" in line) and ("bl" in line) and (".SUBCKT" not in line):
				blank_cell_line = line.split(" ")
				for i in range(0,len(blank_cell_line)):
					if "bl" in blank_cell_line[i]:
						blank_cell_line[i] = "gnd"
					if "net" in blank_cell_line[i]:
						blank_cell_line[i] = "gnd"
				blank_cell = blank_cell + " ".join(blank_cell_line)
			if ("wl" in line) and ("br" in line) and (".SUBCKT" not in line):
				blank_cell_line = line.split(" ")
				for i in range(0,len(blank_cell_line)):
					if "br" in blank_cell_line[i]:
						blank_cell_line[i] = "gnd"
					if "net" in blank_cell_line[i]:
						blank_cell_line[i] = "vdd"
				blank_cell = blank_cell + " ".join(blank_cell_line)
		if (".ENDS" in line) and (cell_flag == 1):
			blank_cell_line = line.split(" ")
			blank_cell_line[1] = "blank_cell"
			blank_cell = blank_cell + " ".join(blank_cell_line)
			cell_flag = 0
	if CMA_mflag == 0:
		bl_arr.append(bl_out)
		br_arr.append(br_out)
		Blcount = 1
	spfile.seek(0)

	PCcountf = 0
	PCcount = 0
	BCcount = 0
	SAcount = 0
	WDcount = 0
	IDFcount = 0
	TGcount = 0
	CMcount = 0
	
	rc = 0

	"""
	Writing of reduced.sp begins here
	"""
	for line in spfile:
		# write blank cell subckt after bit cell subckt
		if ".SUBCKT {}".format(cell_name) in line:
				cell_flag = 1
		if (".ENDS" in line) and (cell_flag == 1):
			cell_flag = 0
			re_spfile.write(line)
			re_spfile.write("\n")
			re_spfile.write(blank_cell)
			re_spfile.write("\n")

		# trimming precharge array 	
		elif ".SUBCKT precharge_array" in line:
			PCA_flag = 1
			trim_line = line.split(" ")
			PCA_line = []
			for i in range(0,len(trim_line)):
				if ("bl" in trim_line[i]) and (trim_line[i] not in bl_arr):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] not in br_arr):
					1 # skip
				else:
					PCA_line.append(trim_line[i])
			re_spfile.write(" ".join(PCA_line))
		elif (".ENDS" in line) and (PCA_flag == 1):
			PCA_flag = 0
			re_spfile.write(line)
		elif ("Xpre_column" in line) and (PCA_flag == 1):
			for i in range(0, Blcount):
				if bl_arr[i] in line:
					re_spfile.write(line)
					PCcountf = 1
				#else:
					# removing Precharge Cells
			if PCcountf == 0:
				PCcount += 1
			PCcountf = 0

		# trimming bitcell array 
		elif ".SUBCKT bitcell_array" in line:
			BCA_flag = 1
			trim_line = line.split(" ")
			BCA_line = []
			for i in range(0,len(trim_line)):
				if ("bl" in trim_line[i]) and (trim_line[i] not in bl_arr):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] not in br_arr):
					1 # skip
				else:
					BCA_line.append(trim_line[i])
			re_spfile.write(" ".join(BCA_line))
		elif (".ENDS" in line) and (BCA_flag == 1):
			BCA_flag = 0
			re_spfile.write(line)
		elif (".ENDS" not in line) and (BCA_flag == 1):
			trim_line = line.split(" ")
			cell_replace = 1
			for i in range(0, Blcount):
				if trim_line[1] == bl_arr[i]:
					re_spfile.write(line)
					cell_replace = 0
			if cell_replace == 1:
				cell_line = []
				for i in range(0,len(trim_line)):
					if ("bl" in trim_line[i]) or ("br" in trim_line[i]):
						1 # skip
					else:
						cell_line.append(trim_line[i])
				cell_line[len(cell_line)-1] = "blank_cell"
				re_spfile.write(' '.join(cell_line))
				re_spfile.write('\n')
				BCcount += 1
		
		# trimming column mux array
		elif ".SUBCKT columnmux_array" in line:
			CMA_flag = 1
			trim_line = line.split(" ")
			CMA_line = []
			for i in range(0,len(trim_line)):
				if ("bl[" in trim_line[i]) and (trim_line[i] not in bl_arr):
					1 # skip
				elif ("br[" in trim_line[i]) and (trim_line[i] not in br_arr):
					1 # skip
				elif ("bl_out[" in trim_line[i]) and (trim_line[i] != bl_out):
					1 # skip
				elif ("br_out[" in trim_line[i]) and (trim_line[i] != br_out):
					1 # skip
				else:
					CMA_line.append(trim_line[i])
			re_spfile.write(" ".join(CMA_line))
		elif (".ENDS" in line) and (CMA_flag == 1):
			CMA_flag = 0
			re_spfile.write(line)
		elif (".ENDS" not in line) and (SA[1] not in line) and (CMA_flag == 1):
			# removing single level Column Muxes
			CMcount += 1
			
		# trimming sense amp array
		elif ".SUBCKT sense_amp_array" in line:
			SAA_flag = 1
			trim_line = line.split(" ")
			SAA_line = []
			for i in range(0,len(trim_line)):
				if ("data_out[" in trim_line[i]) and (trim_line[i] != data_out):
					1 # skip
				elif ("bl" in trim_line[i]) and (trim_line[i] != bl_out):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] != br_out):
					1 # skip
				else:
					SAA_line.append(trim_line[i])
			re_spfile.write(" ".join(SAA_line))
		elif (".ENDS" in line) and (SAA_flag == 1):
			SAA_flag = 0
			re_spfile.write(line)
		elif (".ENDS" not in line) and ("Xsa_d{} ".format(Dvar) not in line) and (SAA_flag == 1):
			# removing Sense Amps
			SAcount += 1
		
		# trimming write driver array
		elif ".SUBCKT write_driver_array" in line:
			WDA_flag = 1
			trim_line = line.split(" ")
			WDA_line = []
			for i in range(0,len(trim_line)):
				if ("data_in[" in trim_line[i]) and (trim_line[i] != data_in):
					1 # skip
				elif ("bl" in trim_line[i]) and (trim_line[i] != bl_out):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] != br_out):
					1 # skip
				else:
					WDA_line.append(trim_line[i])
			re_spfile.write(" ".join(WDA_line))
		elif (".ENDS" in line) and (WDA_flag == 1):
			WDA_flag = 0
			re_spfile.write(line)
		elif (".ENDS" not in line) and ("XXwrite_driver{} ".format(Dvar) not in line) and (WDA_flag == 1):
			# removing Write Drivers
			WDcount += 1
		
		# trimming input data ms-flop array
		elif ".SUBCKT msf_data_in" in line:
			DIFA_flag = 1
			trim_line = line.split(" ")
			DIFA_line = []
			for i in range(0,len(trim_line)):
				if ("DATA[" in trim_line[i]) and (trim_line[i] != DATA):
					1 # skip
				elif ("data_in[" in trim_line[i]) and (trim_line[i] != data_in):
					1 # skip
				elif ("data_in_bar[" in trim_line[i]) and (trim_line[i] != data_in_bar):
					1 # skip
				else:
					DIFA_line.append(trim_line[i])
			re_spfile.write(" ".join(DIFA_line))
		elif (".ENDS" in line) and (DIFA_flag == 1):
			DIFA_flag = 0
			re_spfile.write(line)
		elif (".ENDS" not in line) and ("XXdff{} ".format(Dvar) not in line) and (DIFA_flag == 1):
			# removing Input Data MS-Flops
			IDFcount += 1
		
		# trimming tri gate array
		elif ".SUBCKT tri_gate_array" in line:
			TGA_flag = 1
			trim_line = line.split(" ")
			TGA_line = []
			for i in range(0,len(trim_line)):
				if ("DATA[" in trim_line[i]) and (trim_line[i] != DATA):
					1 # skip
				elif ("tri_in[" in trim_line[i]) and (trim_line[i] != tri_in):
					1 # skip
				else:
					TGA_line.append(trim_line[i])
			re_spfile.write(" ".join(TGA_line))
		elif (".ENDS" in line) and (TGA_flag == 1):
			TGA_flag = 0
			re_spfile.write(line)
		elif (".ENDS" not in line) and ("XXtri_gate{} ".format(Dvar) not in line) and (TGA_flag == 1):
			# removing Tri Gates
			TGcount += 1
			
		################################
		# trimming headers in test bank
		################################
		elif ".SUBCKT bank" in line:
			TBK_flag = 1
			re_spfile.write(line)
		elif (".ENDS" in line) and (TBK_flag == 1):
			TBK_flag = 0
			for i in range(0,word_size-1):
				if "DATA[{}]".format(i) != DATA:
					re_spfile.write("R{} DATA[{}] gnd 0.0001\n".format(i, i))
			re_spfile.write(line)
		elif ("bitcell_array" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			BCA_line = []
			for i in range(0,len(trim_line)):
				if ("bl" in trim_line[i]) and (trim_line[i] not in bl_arr):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] not in br_arr):
					1 # skip
				else:
					BCA_line.append(trim_line[i])
			re_spfile.write(" ".join(BCA_line))
		elif ("precharge_array" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			PCA_line = []
			for i in range(0,len(trim_line)):
				if ("bl" in trim_line[i]) and (trim_line[i] not in bl_arr):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] not in br_arr):
					1 # skip
				else:
					PCA_line.append(trim_line[i])
			re_spfile.write(" ".join(PCA_line))
		elif ("columnmux_array" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			CMA_line = []
			for i in range(0,len(trim_line)):
				if ("bl[" in trim_line[i]) and (trim_line[i] not in bl_arr):
					1 # skip
				elif ("br[" in trim_line[i]) and (trim_line[i] not in br_arr):
					1 # skip
				elif ("bl_out[" in trim_line[i]) and (trim_line[i] != bl_out):
					1 # skip
				elif ("br_out[" in trim_line[i]) and (trim_line[i] != br_out):
					1 # skip
				else:
					CMA_line.append(trim_line[i])
			re_spfile.write(" ".join(CMA_line))
		elif ("sense_amp_array" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			SAA_line = []
			for i in range(0,len(trim_line)):
				if ("data_out[" in trim_line[i]) and (trim_line[i] != data_out):
					1 # skip
				elif ("bl" in trim_line[i]) and (trim_line[i] != bl_out):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] != br_out):
					1 # skip
				else:
					SAA_line.append(trim_line[i])
			re_spfile.write(" ".join(SAA_line))
		elif ("write_driver_array" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			WDA_line = []
			for i in range(0,len(trim_line)):
				if ("data_in[" in trim_line[i]) and (trim_line[i] != data_in):
					1 # skip
				elif ("bl" in trim_line[i]) and (trim_line[i] != bl_out):
					1 # skip
				elif ("br" in trim_line[i]) and (trim_line[i] != br_out):
					1 # skip
				else:
					WDA_line.append(trim_line[i])
			re_spfile.write(" ".join(WDA_line))
		elif ("msf_data_in" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			DIFA_line = []
			for i in range(0,len(trim_line)):
				if ("DATA[" in trim_line[i]) and (trim_line[i] != DATA):
					1 # skip
				elif ("data_in[" in trim_line[i]) and (trim_line[i] != data_in):
					1 # skip
				elif ("data_in_bar[" in trim_line[i]) and (trim_line[i] != data_in_bar):
					1 # skip
				else:
					DIFA_line.append(trim_line[i])
			re_spfile.write(" ".join(DIFA_line))
		elif ("tri_gate_array" in line) and (TBK_flag == 1):
			trim_line = line.split(" ")
			TGA_line = []
			for i in range(0,len(trim_line)):
				if ("DATA[" in trim_line[i]) and (trim_line[i] != DATA):
					1 # skip
				elif ("data_out[" in trim_line[i]) and (trim_line[i] != data_out):
					1 # skip
				else:
					TGA_line.append(trim_line[i])
			re_spfile.write(" ".join(TGA_line))
		
		# otherwise wrtie line
		else:
			re_spfile.write(line)

	# stat and debug information
	"""
	print "Word Size = {}".format(word_size)
	print "{} precharge cells trimmed".format(PCcount)
	print "{} bit cells trimmed".format(BCcount)
	print "{} column muxes trimmed".format(CMcount)
	print "{} sense amplifiers trimmed".format(SAcount)
	print "{} write drivers trimmed".format(WDcount)
	print "{} input data MS-flops trimmed".format(IDFcount)
	print "{} tri gates trimmed".format(TGcount)
	print "# bit lines = {}".format(Blcount)
	print "SA => {}".format(SA)
	print "DIF => {}".format(DIF)
	print "bl_out => {}".format(bl_out)
	print "br_out => {}".format(br_out)
	print "bl_arr => {}".format(bl_arr)
	print "br_arr => {}".format(br_arr)
	print "DATA => {}".format(DATA)
	print "data_out, data_in, data_in_bar => {}, {}, {}".format(data_out, data_in, data_in_bar)
	"""
	
	spfile.close()
	re_spfile.close()
