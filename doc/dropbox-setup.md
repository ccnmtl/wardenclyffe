## How to set up a Wardenclyffe S3 Dropbox Bucket

### S3 bucket

In the AWS Console, create a new S3 bucket with a bucket name that
starts with `ctl-wardenclyffe-dropbox-`.

Note that since S3 bucket names are globally unique, as long as WC has
the ability to read from the bucket, the bucket does not need to be
owned by the CTL account.

You can set up whatever permissions, roles, etc. you need to allow
your users to upload there. The CTL role needs read access. If the S3
bucket is created in the CTL account, that should be
automatic. Otherwise, you will need to make sure that whatever tool
users are using to upload files to the bucket sets them to publicly
readable.

### WC DropBucket

In the
[Wardenclyffe Admin](https://wardenclyffe.ctl.columbia.edu/admin/),
look for 'Drop bucket' and hit 'add'.

You need to give it a name, an optional description, then specify the
S3 bucket name that you set up earlier, a default User (that will be
the "owner" of the videos) and Collection that the videos will end up
in.

## Additional configuration

The two steps above are the only things required. You may want to add
additional configs to the S3 bucket to eg, delete files after a
certain period of time or archive them to Glacier. Wardenclyffe does
not delete the files from the dropbox bucket once it has ingested
them, so you'll want to set something up so they don't just accumulate
forever. However, I'd recommend letting them sit there for at least a
few days before automatically deleting them so we have a bit of a
window to investigate any failures.
