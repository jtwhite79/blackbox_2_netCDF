import os
import sys
from datetime import datetime
import pytz
from pytz import timezone

#--python 3 compatibility
pyver = sys.version_info
if pyver[0] == 3:
	raw_input = input

#--some import error trapping
try:
	import numpy as np
except:
	raise Exception("numpy is required")
try:		
	import netCDF4
except:
	raise Exception("netCDF4 is required")		



class pressure(object):
	'''super class for reading raw wave data and writing to netcdf file
	this class should not be instantiated directly
	'''
	
	def __init__(self):
		self.in_filename = None
		self.out_filename = None
		self.is_baro = None
		self.pressure_units = None
		self.z_units = None
		self.latitude = None
		self.longitude = None
		self.z = None
		self.salinity_ppm = -1.0e+10
		self.utc_second_data = None
		self.pressure_data = None
		self.epoch_start = datetime(year=1970,month=1,day=1,tzinfo=pytz.utc)
		self.data_start = None
		self.valid_pressure_units = ["psi","pascals","atm"]
		self.valid_z_units = ["meters","feet"]
		self.fill_value = np.float32(-1.0e+10)

	@property	
	def offset_seconds(self):
		'''offsets seconds from specified epoch using UTC time
		'''		
		offset = self.data_start - self.epoch_start				
		return offset.seconds


	def time_var(self,ds):
		time_var = ds.createVariable("time","u8",("time",))
		time_var.long_name = ''
		time_var.standard_name = "time"
		time_var.units = "milliseconds since "+self.epoch_start.strftime("%Y-%m-%d %H:%M:%S")
		time_var.calendar = "gregorian"
		time_var.axis = 't'
		time_var.ancillary_variables = ''
		time_var.comment = ''
		time_var[:] = self.utc_second_data
		return time_var


	def longitude_var(self,ds):
		longitude_var = ds.createVariable("longitude","f4",fill_value=self.fill_value)
		longitude_var.long_name = "longitude of sensor"
		longitude_var.standard_name = "longitude"
		longitude_var.units = "degrees east"
		longitude_var.axis = 'X'
		longitude_var.min = np.float32(-180.0)
		longitude_var.max = np.float32(180.0)		
		longitude_var.ancillary_variables = ''
		longitude_var.comment = "longitude 0 equals prime meridian"
		longitude_var[:] = self.longitude
		return longitude_var


	def latitude_var(self,ds):
		latitude_var = ds.createVariable("latitude","f4",fill_value=self.fill_value)
		latitude_var.long_name = "latitude of sensor"
		latitude_var.standard_name = "latitude"
		latitude_var.units = "degrees north"
		latitude_var.axis = 'Y'
		latitude_var.min = np.float32(-90.0)
		latitude_var.max = np.float32(90.0)		
		latitude_var.ancillary_variables = ''
		latitude_var.comment = "latitude 0 equals equator"
		latitude_var = self.latitude
		return latitude_var


	def z_var(self,ds):	
		z_var = ds.createVariable("z","f4",fill_value=self.fill_value)
		z_var.long_name = "altitude of sensor"
		z_var.standard_name = "altitude"	
		z_var.units = self.z_units
		z_var.axis = 'Z'
		z_var.min = np.float32(-11000.0)
		z_var.max = np.float32(9000.0)		
		z_var.ancillary_variables = ''
		z_var.comment = "altitude above NAVD88"
		z_var[:] = self.z
		return z_var


	def pressure_var(self,ds):
		pressure_var = ds.createVariable("pressure","f4",("time",),fill_value=self.fill_value)
		pressure_var.long_name = "sensor pressure record"
		pressure_var.standard_name = "pressure"	
		pressure_var.nodc_name = "pressure".upper()	
		pressure_var.units = self.pressure_units
		pressure_var.scale_factor = np.float32(1.0)
		pressure_var.add_offset = np.float32(0.0)		
		pressure_var.min = np.float32(-10000.0)
		pressure_var.max = np.float32(10000.0)		
		pressure_var.ancillary_variables = ''
		pressure_var.coordinates = "time latitude longitude z"
		pressure_var[:] = self.pressure_data
		return pressure_var


	def write(self):
		assert not os.path.exists(self.out_filename),"out_filename already exists"
		#--create variables and assign data
		ds = netCDF4.Dataset(self.out_filename,'w',format="NETCDF4")
		time_dimen = ds.createDimension("time",len(self.pressure_data))		
		time_var = self.time_var(ds)
		latitude_var = self.latitude_var(ds)
		longitude_var = self.longitude_var(ds)
		z_var = self.z_var(ds)
		pressure_var = self.pressure_var(ds)
		ds.salinity_ppm = np.float32(self.salinity_ppm)		
		

	def get_user_input(self):		
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

		pressure_units = raw_input("what are the pressure units? ("+','.join(self.valid_pressure_units)+")?\n").lower()
		while pressure_units not in self.valid_pressure_units:
			pressure_units = raw_input("what are the pressure units? ("+','.join(self.valid_pressure_units)+")?\n").lower()
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

		z = raw_input("what is the altitude of the sensor?\n")	
		try:
			z = np.float32(z)
		except:
			while True:				
				z = raw_input("what is the altitude of the sensor?\n")	
				try:
					z = np.float32(z)
					break
				except:
					pass	
		self.z = z

		z_units = raw_input("what are the z units (" +','.join(self.valid_z_units)+ ")\n")
		while z_units.lower() not in self.valid_z_units:
			z_units = raw_input("what are the z units (" +','.join(self.valid_z_units)+ ")\n")
		self.z_units = z_units			


		salinity = raw_input("what is the salinity (ppm or mg/l) where these data were collected?\n")	
		try:
			salinity = np.float32(salinity)
		except:
			while True:				
				salinity = raw_input("what is the salinity (ppm or mg/l) where these data were collected?\n")	
				try:
					salinity = np.float32(salinity)
					break
				except:
					pass	
		self.salinity_ppm = salinity

		out_filename = raw_input("what is the output netcdf file name? (enter to use level troll filename with \'.nc\' suffix")		
		if out_filename == '':			
			out_filename = in_filename + ".nc"			
		if os.path.exists(out_filename):
			cont = raw_input("Warning - netcdf4 file "+out_filename+" already exists - overwrite? (y/n)?")
			if not cont:
				out_filename = raw_input("what is the output netcdf file name? (enter to use level troll filename with \'.nc\' suffix")
				if out_filename == '':
					out_filename = self.in_filename + ".nc"
			else:
				try:
					os.remove(out_filename)					
				except:
					raise Exception("unable to remove existing netcdf file: "+out_filename)					
		
		self.out_filename = out_filename


	def read(self):
		raise Exception("read() must be implemented in the derived classes")




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
		f.close()
		self.utc_second_data = data["seconds"] + self.offset_seconds
		self.pressure_data = data["pressure"]
		

	def read_header(self,f):
		''' read the header from the level troll ASCII file
		'''
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
		'''read the first datetime and cast
		'''		
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
		'''set the timezone from the timezone string found in the header - 
		needed to get the times into UTC
		'''
		tz_dict = {"central":"US/Central","eastern":"US/Eastern"}
		for tz_str,tz in tz_dict.iteritems():
			if self.timezone_string.lower().startswith(tz_str):
				self.tzinfo = timezone(tz)
				return				
		raise Exception("could not find a timezone match for "+timezone_string)				



if __name__ == "__main__":
		
	lt = leveltroll()		
	
	#--for testing
	# lt.in_filename = os.path.join("benchmark","data.csv")
	# lt.out_filename = os.path.join("benchmark","data.csv.nc")
	# if os.path.exists(lt.out_filename):
	# 	os.remove(lt.out_filename)
	# lt.is_baro = True
	# lt.pressure_units = "psi"
	# lt.z_units = "meters"
	# lt.longitude = np.float32(0.0)
	# lt.latitude = np.float(0.0)
	# lt.salinity_ppm = np.float32(0.0)
	# lt.z = np.float32(0.0)
	lt.get_user_input()
	lt.read()	
	lt.write()