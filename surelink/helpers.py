import hashlib

# variables for now. think about how to parameterize later

# urls
BROADCAST_URL_BASE = "http://ccnmtl.columbia.edu/broadcast/"
STREAM_URL_BASE = "http://ccnmtl.columbia.edu/stream/"
SURELINK_BASE = "https://surelink.ccnmtl.columbia.edu/video/"

# protections
PUBLIC_MP4_DOWNLOAD = "public-mp4-download"
PUBLIC_MP4_STREAM = "mp4_public_stream"
SECURE_MP4_STREAM = "mp4_secure_stream"


PROTECTION_OPTIONS = [
    dict(value="public-mp4-download",
         label="public mp4/mp3 non-streaming"),
    dict(value="public",
         label="public streaming flv"),
    dict(value="protected",
         label="protected streaming flv/protected mp3 (valid-user)"),
    dict(value="mp4_public_stream",
         label="mp4 public stream"),
    dict(value="mp4_secure_stream",
         label="mp4 secure stream"),
]

AUTHTYPE_OPTIONS = [
    dict(value="", label="None (Public)"),
    dict(value="wikispaces",
         label="Wikispaces (Pamacea auth-domain) [authtype=wikispaces]"),
    dict(value="auth",
         label=("Standard UNI (Pamacea domain incompatible with wikispaces)"
                " [authtype=auth]")),
    dict(value="wind",
         label="WIND [authtype=wind]"),
]


class SureLink:
    def __init__(self, filename, width, height, captions, poster, protection,
                 authtype, protection_key):
        self.filename = filename
        self.width = width
        self.height = height
        self.captions = captions
        self.poster = poster
        self.protection = protection
        self.authtype = authtype
        self.protection_key = protection_key

    def get_protection(self, force_public=False):
        if force_public:
            protection = "public"
        else:
            protection = self.protection
        s = "%s:%s:%s" % (self.filename, protection, self.protection_key)
        return hashlib.sha1(s).hexdigest()

    def player_string(self):
        if self.protection == PUBLIC_MP4_DOWNLOAD:
            return 'download_mp4_v3'
        elif self.protection in (PUBLIC_MP4_STREAM, SECURE_MP4_STREAM):
            return self.protection
        return "v4"

    def captions_string(self):
        if self.captions:
            return "&captions=%s" % self.captions
        return ""

    def authtype_string(self):
        if self.authtype:
            return "&authtype=%s" % self.authtype
        return ""

    def video_options(self):
        if self.poster == 'default_custom_poster':
            if 'secure' in self.filename:
                # secure: parallel dir as video file in /broadcast/posters/
                self.poster = (
                    BROADCAST_URL_BASE + "posters/"
                    + self.filename.replace('.mp4', '.jpg')
                    .replace('.flv', '.jpg'))
            else:
                # insecure: same dir as video file
                self.poster = (
                    BROADCAST_URL_BASE
                    + self.filename.replace('.mp4', '.jpg')
                    .replace('.flv', '.jpg'))

        return ("player=%s&file=%s&width=%d&height=%d&poster=%s%s%s" %
                (self.player_string(), self.filename, self.width, self.height,
                 self.poster, self.captions_string(), self.authtype_string()))

    def src_url(self):
        return ("%sjsembed?%s%s" % (STREAM_URL_BASE, self.video_options(),
                                    self.protection_string()))

    def public_url(self):
        return ("%sflv/%s/OPTIONS/%s" % (
                STREAM_URL_BASE, self.get_protection(force_public=True),
                self.filename))

    def group(self):
        if self.protection.startswith('public'):
            return 'public'
        else:
            return self.protection

    def protection_string(self):
        if self.protection.startswith('public'):
            return "&protection=%s" % self.get_protection(force_public=True)
        return ""

    def public_mp4_download(self):
        return self.protection == PUBLIC_MP4_DOWNLOAD

    ##### Nitty-gritty embed codes! #####

    def basic_embed(self):
        return ("""<script type="text/javascript" src="%s"></script>""" %
                self.src_url())

    def iframe_embed(self):
        return ("""<iframe width="%d" height="%d" src="%s?%s%s" />""" %
                (self.width, self.height + 24, SURELINK_BASE,
                 self.video_options(), self.protection_string()))

    def edblogs_embed(self):
        return """[ccnmtl_video src="%s"]""" % self.src_url()

    def drupal_embed(self):
        return ("%sflv/xdrupalx/OPTIONS/%s" % (STREAM_URL_BASE,
                                               self.filename))

    def mdp_embed(self):
        width_string = ""
        if self.width:
            width_string = "[w]%d" % self.width
        height_string = ""
        if self.height:
            height_string = "[h]%d" % self.height

        if self.public_mp4_download():
            return ("[mp4]%s%s%s%s[mp4]" %
                    (BROADCAST_URL_BASE, self.filename, width_string,
                     height_string))
        else:
            return "[flv]%s%s%s[flv]" % (self.public_url(), width_string,
                                         height_string)
