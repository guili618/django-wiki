import base64
from io import BytesIO

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.urls import reverse
from wiki.core.plugins import registry as plugin_registry
from wiki.models import URLPath
from wiki.plugins.images import models
from wiki.plugins.images.wiki_plugin import ImagePlugin

from ...base import ArticleWebTestUtils, DjangoClientTestBase, RequireRootArticleMixin


class ImageTests(RequireRootArticleMixin, ArticleWebTestUtils, DjangoClientTestBase):

    def setUp(self):
        super().setUp()
        self.article = self.root_article
        # A black 1x1 gif
        self.test_data = "R0lGODlhAQABAIAAAAUEBAAAACwAAAAAAQABAAACAkQBADs="

    def _create_gif_filestream_from_base64(self, str_base64, **kwargs):
        """
        Helper function to create filestream for upload.

        Parameters :
        strData : str, test string data

        Optional Arguments :
        filename : str, Defaults to 'test.txt'
        """
        filename = kwargs.get('filename', 'test.gif')
        data = base64.b64decode(str_base64)
        filedata = BytesIO(data)
        filestream = InMemoryUploadedFile(
            filedata,
            None,
            filename,
            'image',
            len(data),
            None
        )
        return filestream

    def _create_test_image(self, path):
        # Get the form index
        plugin_index = -1
        for cnt, plugin_instance in enumerate(plugin_registry.get_sidebar()):
            if isinstance(plugin_instance, ImagePlugin):
                plugin_index = cnt
                break
        self.assertTrue(plugin_index >= 0, "Image plugin not activated")
        base_edit_url = reverse('wiki:edit', kwargs={'path': path})
        url = base_edit_url + '?f=form{0:d}'.format(plugin_index)
        filestream = self._create_gif_filestream_from_base64(self.test_data)
        response = self.client.post(
            url,
            {
                'unsaved_article_title': self.article.current_revision.title,
                'unsaved_article_content': self.article.current_revision.content,
                'image': filestream,
                'images_save': '1',
            },
        )
        self.assertRedirects(response, base_edit_url)

    def test_index(self):
        url = reverse('wiki:images_index', kwargs={'path': ''})
        response = self.client.get(url,)
        self.assertContains(response, 'Images')

    def test_upload(self):
        """
        Tests that simple file upload uploads correctly
        Uploading a file should preserve the original filename.
        Uploading should not modify file in any way.
        """
        self._create_test_image('')
        # Check the object was created.
        image = models.Image.objects.get()
        image_revision = image.current_revision.imagerevision
        self.assertEqual(image_revision.get_filename(), 'test.gif')
        self.assertEqual(
            image_revision.image.file.read(),
            base64.b64decode(self.test_data)
        )

    def get_article(self, cont, image):
        urlpath = URLPath.create_urlpath(
            URLPath.root(),
            "html_image",
            title="TestImage",
            content=cont
        )
        if image:
            self._create_test_image(urlpath.path)
        return urlpath.article.render()

    def test_image_missing(self):
        output = self.get_article("[image:1]", False)
        expected = (
            '<figure class="thumbnail"><a href="">'
            '<div class="caption"><em>Image not found</em></div>'
            '</a><figcaption class="caption"></figcaption></figure>'
        )
        self.assertEqual(output, expected)

    def test_image_default(self):
        output = self.get_article("[image:1]", True)
        image_rev = models.Image.objects.get().current_revision.imagerevision
        expected = (
            '<figure class="thumbnail">'
            '<a href="' + image_rev.image.name + '">'
            '<img alt="test\.gif" src="cache/.*\.jpg">'
            '</a><figcaption class="caption"></figcaption></figure>'
        )
        self.assertRegexpMatches(output, expected)

    def test_image_large_right(self):
        output = self.get_article("[image:1 align:right size:large]", True)
        image_rev = models.Image.objects.get().current_revision.imagerevision
        expected = (
            '<figure class="thumbnail pull-right">'
            '<a href="' + image_rev.image.name + '">'
            '<img alt="test\.gif" src="cache/.*\.jpg"></a>'
            '<figcaption class="caption"></figcaption></figure>'
        )
        self.assertRegexpMatches(output, expected)

    def test_image_orig(self):
        output = self.get_article("[image:1 size:orig]", True)
        image_rev = models.Image.objects.get().current_revision.imagerevision
        expected = (
            '<figure class="thumbnail">'
            '<a href="' + image_rev.image.name + '">'
            '<img alt="test.gif" src="' + image_rev.image.name + '"></a>'
            '<figcaption class="caption"></figcaption></figure>'
        )
        self.assertEqual(output, expected)
