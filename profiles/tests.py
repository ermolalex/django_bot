from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import  ValidationError

from profiles.models import Profile, Company

# from django.contrib.auth import get_user_model
# User = get_user_model()


class ProfileTestCase(TestCase):
    # @staticmethod
    # def _get_saved(model_obj):
    #     model_obj.save()
    #     model_obj.refresh_from_db()
    #     return model_obj
    #
    # def _test_get_meta_title(self):
    #     parent_title, child_title = "P title", "C title"
    #     parent_meta_title, child_meta_title = "P meta title", "C meta title"
    #     parent_product = ProductFactory(
    #         structure=Product.PARENT, title=parent_title, meta_title=parent_meta_title
    #     )
    #     child_product = ProductFactory(
    #         structure=Product.CHILD,
    #         title=child_title,
    #         meta_title=child_meta_title,
    #         parent=parent_product,
    #     )
    #     self.assertEqual(child_product.get_meta_title(), child_meta_title)
    #     child_product.meta_title = ""
    #     self.assertEqual(
    #         self._get_saved(child_product).get_meta_title(), parent_meta_title
    #     )
    #     parent_product.meta_title = ""
    #     child_product.parent = self._get_saved(parent_product)
    #     self.assertEqual(self._get_saved(child_product).get_meta_title(), child_title)
    #
    # def _test_get_meta_description(self):
    #     parent_description, child_description = "P description", "C description"
    #     parent_meta_description, child_meta_description = (
    #         "P meta description",
    #         "C meta description",
    #     )
    #     parent_product = ProductFactory(
    #         structure=Product.PARENT,
    #         description=parent_description,
    #         meta_description=parent_meta_description,
    #     )
    #     child_product = ProductFactory(
    #         structure=Product.CHILD,
    #         description=child_description,
    #         meta_description=child_meta_description,
    #         parent=parent_product,
    #     )
    #     self.assertEqual(child_product.get_meta_description(), child_meta_description)
    #     child_product.meta_description = ""
    #     self.assertEqual(
    #         self._get_saved(child_product).get_meta_description(),
    #         parent_meta_description,
    #     )
    #     parent_product.meta_description = ""
    #     child_product.parent = self._get_saved(parent_product)
    #     self.assertEqual(
    #         self._get_saved(child_product).get_meta_description(), child_description
    #     )
    #
    # def _test_product_code(self):
    #     parent_title, child_title = "P title", "C title"
    #     parent_meta_title, child_meta_title = "P meta title", "C meta title"
    #     parent_product = ProductFactory(
    #         structure=Product.PARENT, title=parent_title, meta_title=parent_meta_title
    #     )
    #     child_product = ProductFactory(
    #         structure=Product.CHILD,
    #         title=child_title,
    #         meta_title=child_meta_title,
    #         parent=parent_product,
    #     )
    #     self.assertIsNone(parent_product.code)
    #     self.assertEqual(child_product.code, parent_product.code)
    #
    #     parent_product.code = "henk"
    #     parent_product.save()
    #
    #     parent = Product.objects.get(code="henk")
    #     self.assertEqual(parent.structure, Product.PARENT)
    #     self.assertEqual(parent_product.pk, parent.pk)
    #
    #     with self.assertRaises(IntegrityError):
    #         child_product.code = "henk"
    #         child_product.save()
    #


    def test_profile_validation(self):
        prof = Profile(username="Sa:;,sa")
        with self.assertRaises(ValidationError):
            prof.full_clean()



    def test_profile_creation(self):
        prof = Profile(username="Sasa")
        prof.save()
        self.assertEqual(prof.username, "Sasa")

        prof2 = Profile(username="Sasa")
        with self.assertRaises(IntegrityError):
            prof2.save()



    # def test_category_creation(self):
    #     print("********* Cat *********")
    #     root_category = create_from_breadcrumbs('Food')
    #     cheese_category = create_from_breadcrumbs('Food > Cheese')
    #     milk_category = create_from_breadcrumbs('Food > Milk')
    #     fruit_category = create_from_breadcrumbs('Fruit')
    #     create_from_breadcrumbs('Fruit > Apple')
    #     create_from_breadcrumbs('Fruit > Banana')
    #     print(f"{cheese_category.name=}, {cheese_category.depth=}, {cheese_category.path=} ")
    #
    #     categories = Category.get_tree()
    #     print(categories)
    #     categories = categories.for_menu()
    #     print(categories)
    #
    #     # cat_list = []
    #     # root_nodes = Category.get_root_nodes()
    #     # _ = Category.get_children()
    #     # for n in root_nodes:
    #     #     cat_list.append(n)
    #     #     if n.has_children():
    #     #         ch_list = []
    #     #         for ch in n.get_children():
    #     #             ch_list.append(ch)
    #     #
    #
    #
    #     self.assertTrue(True)

        # root = CategoryFactory()
        # self.assertIn("Cat", root.name)
        #
        # child = CategoryFactory()
        # root.add_child(instance=root)
        # self.assertIn("Cat", child.name)

