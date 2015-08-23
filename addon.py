# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re
import xbmcplugin, xbmcgui, xbmcvfs, xbmcaddon
import xml.etree.ElementTree as ET
import string
import urlparse
import datetime

base_surl = 'http://api.sovok.tv/v2.3/xml/'
sid = ''
tpath = xbmc.translatePath('special://profile/addon_data/%s/' % xbmcaddon.Addon().getAddonInfo('id'))
# thumb = os.path.join( addon.getAddonInfo('path'), "icon.png" )

def send_request(name, param = None) :
	req = base_surl + name
	if param :
		req += '?' + param
	if sid :
		if param :
			req += '&' + sid
		else :
			req += '?' + sid

	res = urllib.urlopen(req).read()
	if (res.find("<response><error><message>You are not logged") >= 0 or \
	   res.find("<response><error><message>Another client with you login was logged") >= 0) and \
	   name != 'login' :
		sovok_login()
		res = send_request(name, param)
	return res



def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

 
def get_ch_url(cid) :
	global sid
	f = xbmcvfs.File(tpath+'sid', 'r')
	sid = f.read()
	f.close()
	return send_request('get_url', 'cid='+cid)

def get_archive_url(cid, utime) :
	global sid
	f = xbmcvfs.File(tpath+'sid', 'r')
	sid = f.read()
	f.close()
	print 'archive_next', 'cid='+cid+'&time='+utime
	#return send_request('archive_next', 'cid='+cid+'&time='+utime)
	return send_request('get_url', 'cid='+cid+'&gmt='+utime)

def start_play(cid, utime = None, title = None, icon = None) :
	if not utime :
		ures = get_ch_url(cid)
	else :
		ures = get_archive_url(cid, utime)
	print ures
	res = ET.fromstring(ures)

	if res.find('error') != None :
		#sovok_login()
		if not utime :
			ures = get_ch_url(cid)
		else :
			ures = get_archive_url(cid, utime)

		res = ET.fromstring(ures)
		
	try :
		stream_url = res.find('.//url').text
	except :
		print 'no url returned:'
		print ures
		msg = 'unknow error'
		if res.find('.//message') != None :
			msg = res.find('.//message').text
		xbmcgui.Dialog().notification('Error', msg, xbmcgui.NOTIFICATION_ERROR);
		return
		
	if stream_url == 'protected' :
		res = send_request('get_url', 'cid='+cid+'&protect_code=0000')
		res = ET.fromstring(res)
		stream_url = res.find('url').text
 
	stream_url = string.replace(stream_url, 'http/ts', 'http')
	stream_url = string.split(stream_url, ' ')[0]
	if not title :
		listitem = xbmcgui.ListItem('zzz')
	else :          
		print(str(title))                          
		listitem=xbmcgui.ListItem(title, iconImage=icon, thumbnailImage=icon, path=stream_url)
		listitem.setInfo(type='video', infoLabels={'title': title })
	
	#listitem.setInfo('duration', '100')
	#listitem.addStreamInfo('video', { 'duration': 100 } )
	#xbmc.Player().play(stream_url, listitem)
	#xbmc.Player().play(stream_url+'|noshout=true', listitem)
	#xbmc.Player().play(stream_url+'|'+urllib.urlencode( {'encoding' : 'UTF-8'} , listitem))
	#xbmc.Player().play(stream_url+'|'+urllib.urlencode( {'Content-Type' : 'application/octet-stream; charset=UTF-8'} , listitem))

	#listitem.setInfo('duration', '100')
	#listitem.addStreamInfo('video', { 'duration': 100 } )
	#item.HasProperty("StartPercent")
	safe = xbmcaddon.Addon().getSetting('safe')
	if safe and safe == 'true' :
		stream_url += '|noshout=true'
	xbmc.Player().play(stream_url, listitem)
	#xbmc.Player().play(stream_url+'|'+urllib.urlencode( {'encoding' : 'UTF-8'} , listitem))
	

def sovok_login() :
	global sid
	addon = xbmcaddon.Addon()
	login = addon.getSetting('login')
	pwd = addon.getSetting('password')
	if login == None or login=='' :
		login = '1111'
		pwd = '1111'
		addon.setSetting('login', login)
		addon.setSetting('password', login)

	res = send_request('login', 'login=%s&pass=%s' % (login,pwd) )
	print res
	res = ET.fromstring(res)
	sid = '&' + res.find('sid_name').text + '=' + res.find('sid').text
	f = xbmcvfs.File(tpath+'sid','w')
	f.write(sid)
	f.close()

#------ main

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
cid = args.get('cid', None);
icon = args.get('icon', None);
group = args.get('group', None);
archive = args.get('archive', None);
title = args.get('title', None);
if archive != None :
	archive = int(archive[0])
if icon != None :
	icon = (icon[0])
if title != None :
	title = (title[0])
if archive == None :
	archive = 0
date = args.get('date', None);
utime = args.get('utime', None);

print 'cid: '+str(cid)+' group: '+str(group)+' archive: '+str(archive)+ ' icon: ' +str(icon)

if cid and (not archive) and (not utime) :
	start_play(cid[0])
	
elif cid and utime:
	print 'playing archive'
	print cid[0]
	print utime[0]
	start_play(cid[0], utime[0], title, icon)

elif cid and date :
	f = xbmcvfs.File(tpath+'sid', 'r')
	sid = f.read()
	f.close()

	res = send_request('epg', 'cid='+cid[0]+'&day='+date[0])
	res = ET.fromstring(res)

	cur_time = int(res.find('servertime').text)

	for ech in res.findall('.//item') :
		if int(ech.find('ut_start').text) < cur_time :
			url = build_url({'utime': int(ech.find('ut_start').text), 'cid': cid[0], 'title': unicode(ech.find('progname').text).encode('utf-8'), 'icon' : icon })
			li = xbmcgui.ListItem(ech.find('t_start').text + '   ' + ech.find('progname').text, iconImage=icon, thumbnailImage=icon)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder = 1)
	xbmcplugin.endOfDirectory(addon_handle)
	
elif cid and archive :
	day = datetime.date.today()
	for i in range(8) :
		url = build_url({'cid': cid[0], 'date': day.strftime('%d%m%y'), 'archive': archive, 'icon' : icon })
		li = xbmcgui.ListItem(day.strftime('%d/%m/%y'), iconImage=icon, thumbnailImage=icon)
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder = 1)
		day = datetime.date.fromordinal(day.toordinal()-1)
	xbmcplugin.endOfDirectory(addon_handle)

elif group :
	f = xbmcvfs.File(tpath+'chlist', 'r')
	res = f.read()
	f.close()
	res = ET.fromstring(res)
	for egr in res.findall('.//groups/item') :
		if egr.find('./id').text == group[0] :
			for ech in egr.findall('.//item') :
				if ech.find('./is_video') != None and (not archive or ech.find('./have_archive').text=='1') :
					
					icon = ech.find('icon').text
					if icon[:4] != 'http':
						icon = 'http://%s%s' % ('sovok.tv', icon)
					url = build_url({'cid': int(ech.find('id').text), 'archive': archive, 'icon' : icon })
					li = xbmcgui.ListItem(ech.find('name').text, iconImage=icon, thumbnailImage=icon)
					xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder = archive)

	xbmcplugin.endOfDirectory(addon_handle)

else :
	xbmcplugin.setContent(addon_handle, 'movies')

	if not archive :
		#sovok_login()
		res = send_request('channel_list')
		if not xbmcvfs.exists(tpath) :
			xbmcvfs.mkdir(tpath)
		f = xbmcvfs.File(tpath+'chlist','w')
		if not f :
			print "can't create channels file!!!"
		else :
			print "writting channels to "+tpath+'chlist'
		f.write(res)
		f.close()
	else :
		f = xbmcvfs.File(tpath+'sid', 'r')
		sid = f.read()
		f.close()
		f = xbmcvfs.File(tpath+'chlist','r')
		res = f.read()
		f.close()
		
	res = ET.fromstring(res)

	if not archive :
		url = build_url({'archive': 1 })
		li = xbmcgui.ListItem(u'Архив', iconImage='DefaultVideo.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder = 1)

	for ech in res.findall('.//groups/item') :
		if ech.find('./is_video') != None :
			pass
		elif archive and max(map(int, ech.find('.//item/have_archive').text))==0 :
			pass
		else :
			url = build_url({'group': int(ech.find('id').text), 'archive': archive })
			li = xbmcgui.ListItem(ech.find('name').text, iconImage='DefaultVideo.png')
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder = 1)
	xbmcplugin.endOfDirectory(addon_handle)
