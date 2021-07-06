import datetime
import os
import hashlib
from lxml import etree

def get_utc_now():
	return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def get_size(f :str) -> int:
	''' Compute bytesize of a file
	'''    
	return os.path.getsize(f)

def get_checksum(f : str, checksum_type='MD5') -> str:
	''' Compute the checksum for the FileSec
	Note: Official checksums supported by METS: Adler-32 CRC32 HAVAL MD5 MNP SHA-1 SHA-256 SHA-384 SHA-512 TIGER WHIRLPOOL
	'''
	checksums = {
		'MD5': hashlib.md5,
		'SHA-1': hashlib.sha1,
		'SHA-256': hashlib.sha256,
		'SHA-384': hashlib.sha384,
		'SHA-512': hashlib.sha512,
	}

	if checksum_type in checksums:
		return checksums[checksum_type](open(f, 'rb').read()).hexdigest()
	else:
		return None

def adjust_ark_name(ark):
	return ark.replace('/', '-').replace('ark:', '')

def update_mets_file(new_package_dir, old_mets_path, parser):

	new_mets_path = new_package_dir + '/' + old_mets_path.split('/')[-1]
	mets_tree = etree.parse(new_mets_path, parser).getroot()
	alto_filegrp = mets_tree.find(".//{http://www.loc.gov/METS/}fileGrp[@ID='ALTOGRP']")
	if alto_filegrp:
		alto_entries = alto_filegrp.findall('.//{http://www.loc.gov/METS/}file')
		for alto_entry in alto_entries:
			checksum_type = alto_entry.attrib['CHECKSUMTYPE']

			# Get FLocat
			flocat = alto_entry.find('.//{http://www.loc.gov/METS/}FLocat')
			alto_path = flocat.attrib['{http://www.w3.org/1999/xlink}href'].replace('file://','')
			alto_path = os.path.join(new_package_dir, alto_path)

			# Attribute: Created
			new_created = get_utc_now()

			# Attribute: Size
			new_size = get_size(alto_path)

			# Attribute: Checksum
			new_checksum = get_checksum(alto_path, checksum_type)
			if not new_checksum:
				# problem
				pass

			# Change all attributes on file element
			alto_entry.attrib['CREATED']  = new_created
			alto_entry.attrib['SIZE']     = str(new_size)
			alto_entry.attrib['CHECKSUM'] = new_checksum
	
	metshdr = mets_tree.find(".//{http://www.loc.gov/METS/}metsHdr")
	metshdr.attrib['LASTMODDATE'] = get_utc_now()
	
	# write new mets file
	mets_tree_str = etree.tostring(mets_tree, pretty_print=True, xml_declaration=True, encoding="utf-8")
	with open(new_mets_path, 'wb') as f:
		f.write(mets_tree_str)

