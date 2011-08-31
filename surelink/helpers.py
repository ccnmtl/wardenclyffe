import hashlib

def protection(filename,group,protection_key):
    s = "%s:%s:%s" % (filename,group,protection_key)
    return hashlib.sha1(s).hexdigest()        

def protection_string(filename,group,protection_key):
    if group.startswith('public'):
        return "&protection=%s" % protection(filename,'public',protection_key)
    return ""

def video_options(protection,file,width,height,poster,player=None,
                  captions=None,authtype=None):
    if protection == "public-mp4-download":
        player = 'download_mp4_v3'
    else:
        if player is None:
            player = 'v3'

    if poster == 'default_custom_poster':
        if 'secure' not in file:
            # secure: parallel dir as video file in /broadcast/posters/
            poster = "http://ccnmtl.columbia.edu/broadcast/posters/" + file.replace('.mp4','.jpg').replace('.flv','.jpg')
        else:
            # insecure: same dir as video file
            poster = "http://ccnmtl.columbia.edu/broadcast/" + file.replace('.mp4','.jpg').replace('.flv','.jpg')
    captions_string = ""
    if captions:
        captions_string = "&captions=%s" % captions

    authtype_string = ""
    if authtype:
        authtype_string = "&authtype=%s" % authtype
    return "player=%s&file=%s&width=%d&height=%d&poster=%s%s%s" % \
        (player,file,width,height,poster,captions_string,authtype_string)
