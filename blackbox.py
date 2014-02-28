import os
from datetime import datetime
import pytz
from pytz import timezone
from dateutil.relativedelta import relativedelta
import numpy as np
from netCDF4 import Dataset

'''
from Scientific.IO import NetCDF
nc = NetCDF.NetCDFFile(“ test.nc”, 'w')
nc.createDimension('recNum', None)
tmpk = nc.createVariable('temperature', Numeric.Float, ('recNum',) )
tmpk.long_name = 'Temperature'
tmpk.units = 'Kelvin'
nc.close()

from Scientific.IO import NetCDF
nc = NetCDF.NetCDFFile(“ test.nc”, 'a')
recNum = nc.dimensions[“recNum”]
tmpk = nc.variables[“ temperature”]
tmpk[0] = 273.01
tmpk[1] = 300.00
nc.close()

'''


class nodc_var(object):
	def __init__(self,dtype,standard_name,units,fillvalue,comment):
		assert dtype in [np.int64,np.float32,np.float64]
		assert units in ["meters","feet","degrees north","degrees south","PSI","Pascals","ATM"] #more?
		self.dtype = dtype
		self.long_name = ""
		self.standard_name = standard_name
		self.units = units 		
		self.axis = ""
		self.ancillary_variables = ""
		self.comment = ""
		self.FillValue = ""


class pressure_time(nodc_var):
	def __init__(self):		
		super(pressure_time,self).__init__(dtype,standard_name,units,fillvalue,comment)
		self.axis = 'T'
		#self.epoch = need to inherit from pressure class
		self.calendar = "gregorian"		



class pressure(object):
	
	def __init__(self):
		self.in_filename = None
		self.is_baro = None
		self.pressure_units = None
		self.latitude = None
		self.longitude = None
		self.salinity_ppm = -1.0e+10
		self.utc_second_data = None
		self.pressure_data = None
		self.epoch_start = datetime(year=1970,month=1,day=1,tzinfo=pytz.utc)
		self.data_start = None

	@property	
	def offset_seconds(self):
		'''offsets seconds from specified epoch using UTC time
		'''		
		offset = self.data_start - self.epoch_start				
		return offset.seconds

	def get_input(self):
		
		in_filename = raw_input("level troll filename\n")
		while not os.path.exists(in_filename):
			print "file",in_filename,"does not exists - try again"
			in_filename = raw_input("level troll filename\n")
		self.in_filename = in_filename

		is_baro = raw_input("is this a barometric correction dataset? (y/n)\n").lower()
		while is_baro not in ['y','n']:
			is_baro = raw_input("is this a barometric correction dataset? (y/n)\n").lower()
		if is_baro == 'y':
			self.is_baro = True
		else:
			self.is_baro = False							

		pressure_units = raw_input("what are the pressure units? (PSI,Pascals,ATM)?\n").lower()
		while pressure_units not in ["psi","pascals","atm"]:
			raw_input("what are the pressure units? (PSI,Pascals,ATM)?\n").lower()
		self.pressure_units = pressure_units

		latitude = raw_input("what is the latitude (DD) where these data were collected?\n")	
		try:
			latitude = np.float32(latitude)
		except:
			while True:				
				latitude = raw_input("what is the latitude (DD) where these data were collected?\n")	
				try:
					latitude = np.float32(latitude)
					break
				except:
					pass					
		self.latitude = latitude

		longitude = raw_input("what is the longitude (DD) where these data were collected?\n")	
		try:
			longitude = np.float32(longitude)
		except:
			while True:				
				longitude = raw_input("what is the longitude (DD) where these data were collected?\n")	
				try:
					longitude = np.float32(longitude)
					break
				except:
					pass	
		self.longitude = longitude

		salinity = raw_input("what is the salinity (ppm or mg/l) where these data were collected?\n")	
		try:
			longitude = np.float32(salinity)
		except:
			while True:				
				salinity = raw_input("what is the salinity (DD) where these data were collected?\n")	
				try:
					longitude = np.float32(longitude)
					break
				except:
					pass	
		self.salinity_ppm = salinity


	def load_txt(self):
		raise Exception("loadtxt() must be implemented in the child class")




class leveltroll(pressure):
	'''derived class for leveltroll ascii files
	'''
	def __init__(self):
		self.numpy_dtype = np.dtype([("seconds",np.float32),("pressure",np.float32)])
		self.record_start_marker = "date and time,seconds"
		self.timezone_marker = "time zone"
		self.timezone_string = None
		super(leveltroll,self).__init__()


	def read(self):
		'''load the data from in_filename
		only parse the initial datetime = much faster
		'''
		f = open(self.in_filename,'rU')
		self.read_header(f)
		self.data_start = self.read_datetime(f)
		data = np.genfromtxt(f,dtype=self.numpy_dtype,delimiter=',',usecols=[1,2])
		
		self.utc_second_data = data["seconds"] + self.offset_seconds
		self.pressure_data = data["pressure"]

		f.close()


	def read_header(self,f):
		line = ""
		line_count = 0	
		while not line.lower().startswith(self.record_start_marker):
			line = f.readline()			
			line_count += 1
			if line.lower().startswith(self.timezone_marker):
				self.timezone_string = line.split(':')[1].strip()		
		if self.timezone_string is None:
			raise Exception("ERROR - could not find time zone in file "+\
				self.in_filename+" header before line "+str(line_count)+'\n') 
		self.set_timezone()		
		

	def read_datetime(self,f):
		#to cast the date time strings to datetime objecs
		dt_fmt = "%m/%d/%Y %I:%M:%S %p "
		dt_converter = lambda x: datetime.strptime(str(x),dt_fmt)\
			.replace(tzinfo=self.tzinfo)
		reset_point = f.tell()			
		line = f.readline()			
		raw = line.strip().split(',')
		dt_str = raw[0]
		try:
			data_start = dt_converter(dt_str)
		except Exception as e:
			raise Exception("ERROR - cannot parse first date time stamp: "+str(td_str)+" using format: "+dt_fmt+'\n')

		f.seek(reset_point)
		return data_start


	def set_timezone(self):
		tz_dict = {"central":"US/Central","eastern":"US/Eastern"}
		for tz_str,tz in tz_dict.iteritems():
			if self.timezone_string.lower().startswith(tz_str):
				self.tzinfo = timezone(tz)
				return				
		raise Exception("could not find a timezone match for "+timezone_string)				






if __name__ == "__main__":
	lt = leveltroll()		
	lt.in_filename = os.path.join("benchmark","data.csv")
	lt.read()	