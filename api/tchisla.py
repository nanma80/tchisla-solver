import json, gzip
from urllib import request

__all__ = []

API_BASE = 'http://www.euclidea.xyz/api/v1/game/numbers/'
API_SINGLE_RECORD = API_BASE + 'solutions/records?query=[{},{}]'
API_NUMBER_RECORDS = API_BASE + 'solutions/records?query={}'
API_BATCH_RECORDS = API_BASE + 'solutions/records?query={{gte:{},lte:{}}}'

CHUNK_SIZE = 131072

def singleRecord(target, digit, verbose = False):
	url = API_SINGLE_RECORD.format(target, digit)
	content = _request(url, verbose)
	records = content['records']
	return int(records[0]['digits_count']) if records else None

def numberRecords(target, verbose = False):
	url = API_NUMBER_RECORDS.format(target)
	content = _request(url, verbose)
	records = content['records']
	wrs = {}
	for x in records:
		rtarget = int(x['target'])
		digit = int(x['digits'])
		record = int(x['digits_count'])
		if target == rtarget:
			wrs[digit] = record
	return wrs

def batchRecords(start, end, verbose = False):
	url = API_BATCH_RECORDS.format(start, end)
	content = _request(url, verbose)
	records = content['records']
	wrs = {}
	for digit in range(1, 10):
		wrs[digit] = {}
	for x in records:
		target = int(x['target'])
		digit = int(x['digits'])
		record = int(x['digits_count'])
		if target in range(1, 1000000000) and digit in range(1, 10):
			wrs[digit][target] = record
	for digit in range(1, 10):
		for length in range(1, 10):
			target = int(str(digit) * length)
			if target in range(start, end + 1) and target not in wrs[digit]:
				wrs[digit][target] = length
	return wrs


def _request(url, verbose = False):
	req = request.Request(url)
	req.add_header('Accept-Encoding', 'gzip, deflate')
	if verbose:
		print('Fetching WR...')
	r = request.urlopen(req)
	m = r.info()
	chunks = []
	read = 0
	while 1:
		chunk = r.read(CHUNK_SIZE)
		if not chunk:
			break
		read += len(chunk)
		chunks.append(chunk)
		if verbose:
			print('\r{} bytes read'.format(read), end='')
	if verbose:
		print()
	data = b''.join(chunks)
	if m['Content-Encoding'] == 'gzip':
		data = gzip.decompress(data)
	return json.loads(data.decode('utf-8'))
