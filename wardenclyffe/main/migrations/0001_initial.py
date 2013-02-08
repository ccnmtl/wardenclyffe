# encoding: utf-8
# flake8: noqa
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Series'
        db.create_table('main_series', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django_extensions.db.fields.CreationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django_extensions.db.fields.ModificationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('creator', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('contributor', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('license', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('uuid', self.gf('django_extensions.db.fields.UUIDField')(max_length=36, blank=True)),
        ))
        db.send_create_signal('main', ['Series'])

        # Adding model 'Video'
        db.create_table('main_video', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django_extensions.db.fields.CreationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django_extensions.db.fields.ModificationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('series', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Series'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('creator', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('subject', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
            ('license', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('language', self.gf('django.db.models.fields.CharField')(default='', max_length=256, blank=True)),
            ('uuid', self.gf('django_extensions.db.fields.UUIDField')(max_length=36, blank=True)),
        ))
        db.send_create_signal('main', ['Video'])

        # Adding model 'File'
        db.create_table('main_file', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django_extensions.db.fields.CreationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django_extensions.db.fields.ModificationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Video'])),
            ('label', self.gf('django.db.models.fields.CharField')(default='', max_length=256, null=True, blank=True)),
            ('url', self.gf('django.db.models.fields.URLField')(default='', max_length=2000, null=True, blank=True)),
            ('cap', self.gf('django.db.models.fields.CharField')(default='', max_length=256, null=True, blank=True)),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=256, null=True, blank=True)),
            ('location_type', self.gf('django.db.models.fields.CharField')(default='tahoe', max_length=256)),
        ))
        db.send_create_signal('main', ['File'])

        # Adding model 'Metadata'
        db.create_table('main_metadata', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.File'])),
            ('field', self.gf('django.db.models.fields.CharField')(default='', max_length=256)),
            ('value', self.gf('django.db.models.fields.TextField')(default='', null=True, blank=True)),
        ))
        db.send_create_signal('main', ['Metadata'])

        # Adding model 'Operation'
        db.create_table('main_operation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django_extensions.db.fields.CreationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django_extensions.db.fields.ModificationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Video'])),
            ('action', self.gf('django.db.models.fields.CharField')(default='', max_length=256)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='in progress', max_length=256)),
            ('params', self.gf('django.db.models.fields.TextField')(default='')),
            ('uuid', self.gf('django_extensions.db.fields.UUIDField')(max_length=36, blank=True)),
        ))
        db.send_create_signal('main', ['Operation'])

        # Adding model 'OperationFile'
        db.create_table('main_operationfile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('operation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Operation'])),
            ('file', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.File'])),
        ))
        db.send_create_signal('main', ['OperationFile'])

        # Adding model 'OperationLog'
        db.create_table('main_operationlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django_extensions.db.fields.CreationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django_extensions.db.fields.ModificationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('operation', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Operation'])),
            ('info', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal('main', ['OperationLog'])

        # Adding model 'Image'
        db.create_table('main_image', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django_extensions.db.fields.CreationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django_extensions.db.fields.ModificationDateTimeField')(default=datetime.datetime.now, blank=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Video'])),
            ('image', self.gf('sorl.thumbnail.fields.ImageWithThumbnailsField')(max_length=100)),
            ('_order', self.gf('django.db.models.fields.IntegerField')(default=0)),
        ))
        db.send_create_signal('main', ['Image'])

        # Adding model 'Poster'
        db.create_table('main_poster', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('video', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Video'])),
            ('image', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Image'])),
        ))
        db.send_create_signal('main', ['Poster'])


    def backwards(self, orm):
        
        # Deleting model 'Series'
        db.delete_table('main_series')

        # Deleting model 'Video'
        db.delete_table('main_video')

        # Deleting model 'File'
        db.delete_table('main_file')

        # Deleting model 'Metadata'
        db.delete_table('main_metadata')

        # Deleting model 'Operation'
        db.delete_table('main_operation')

        # Deleting model 'OperationFile'
        db.delete_table('main_operationfile')

        # Deleting model 'OperationLog'
        db.delete_table('main_operationlog')

        # Deleting model 'Image'
        db.delete_table('main_image')

        # Deleting model 'Poster'
        db.delete_table('main_poster')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.file': {
            'Meta': {'object_name': 'File'},
            'cap': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'created': ('django_extensions.db.fields.CreationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'location_type': ('django.db.models.fields.CharField', [], {'default': "'tahoe'", 'max_length': '256'}),
            'modified': ('django_extensions.db.fields.ModificationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'default': "''", 'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Video']"})
        },
        'main.image': {
            'Meta': {'ordering': "('_order',)", 'object_name': 'Image'},
            '_order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created': ('django_extensions.db.fields.CreationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('sorl.thumbnail.fields.ImageWithThumbnailsField', [], {'max_length': '100'}),
            'modified': ('django_extensions.db.fields.ModificationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Video']"})
        },
        'main.metadata': {
            'Meta': {'ordering': "('field',)", 'object_name': 'Metadata'},
            'field': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256'}),
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'value': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'})
        },
        'main.operation': {
            'Meta': {'object_name': 'Operation'},
            'action': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256'}),
            'created': ('django_extensions.db.fields.CreationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django_extensions.db.fields.ModificationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'params': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'in progress'", 'max_length': '256'}),
            'uuid': ('django_extensions.db.fields.UUIDField', [], {'max_length': '36', 'blank': 'True'}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Video']"})
        },
        'main.operationfile': {
            'Meta': {'object_name': 'OperationFile'},
            'file': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.File']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'operation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Operation']"})
        },
        'main.operationlog': {
            'Meta': {'object_name': 'OperationLog'},
            'created': ('django_extensions.db.fields.CreationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'info': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'modified': ('django_extensions.db.fields.ModificationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'operation': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Operation']"})
        },
        'main.poster': {
            'Meta': {'object_name': 'Poster'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Image']"}),
            'video': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Video']"})
        },
        'main.series': {
            'Meta': {'object_name': 'Series'},
            'contributor': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'created': ('django_extensions.db.fields.CreationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'modified': ('django_extensions.db.fields.ModificationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'subject': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'uuid': ('django_extensions.db.fields.UUIDField', [], {'max_length': '36', 'blank': 'True'})
        },
        'main.video': {
            'Meta': {'object_name': 'Video'},
            'created': ('django_extensions.db.fields.CreationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creator': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'license': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '256', 'blank': 'True'}),
            'modified': ('django_extensions.db.fields.ModificationDateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'series': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Series']"}),
            'subject': ('django.db.models.fields.TextField', [], {'default': "''", 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'uuid': ('django_extensions.db.fields.UUIDField', [], {'max_length': '36', 'blank': 'True'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['main']
