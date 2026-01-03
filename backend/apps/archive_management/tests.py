"""
档案管理模块测试文件
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from backend.apps.production_management.models import Project
from backend.apps.customer_management.models import Client
from backend.apps.delivery_customer.models import DeliveryRecord, DeliveryFile
from backend.apps.customer_management.models import (
    ArchiveCategory,
    ArchiveProjectArchive,
    ProjectArchiveDocument,
    ArchivePushRecord,
    AdministrativeArchive,
    ArchiveBorrow,
)

User = get_user_model()


class ArchiveCategoryTestCase(TestCase):
    """档案分类测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.category = ArchiveCategory.objects.create(
            name='测试分类',
            code='TEST001',
            category_type='project',
            created_by=self.user
        )
    
    def test_category_creation(self):
        """测试分类创建"""
        self.assertEqual(self.category.name, '测试分类')
        self.assertEqual(self.category.code, 'TEST001')
        self.assertEqual(self.category.category_type, 'project')
    
    def test_category_archive_count(self):
        """测试分类档案数量统计"""
        count = self.category.archive_count
        self.assertIsInstance(count, int)


class ArchivePushRecordTestCase(TestCase):
    """交付推送记录测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client.objects.create(
            name='测试客户',
            created_by=self.user
        )
        self.project = Project.objects.create(
            project_number='VIH-2024-001',
            project_name='测试项目',
            client=self.client,
            created_by=self.user,
            status='in_progress'
        )
        self.delivery = DeliveryRecord.objects.create(
            delivery_number='DEL202401010001',
            title='测试交付',
            project=self.project,
            client=self.client,
            recipient_name='测试收件人',
            recipient_email='test@example.com',
            delivery_method='email',
            status='confirmed',
            created_by=self.user
        )
    
    def test_push_record_creation(self):
        """测试推送记录创建"""
        push_record = ArchivePushRecord.objects.create(
            delivery_record=self.delivery,
            project=self.project,
            push_status='pending'
        )
        self.assertEqual(push_record.delivery_record, self.delivery)
        self.assertEqual(push_record.project, self.project)
        self.assertEqual(push_record.push_status, 'pending')


class ProjectArchiveDocumentTestCase(TestCase):
    """项目档案文档测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client.objects.create(
            name='测试客户',
            created_by=self.user
        )
        self.project = Project.objects.create(
            project_number='VIH-2024-001',
            project_name='测试项目',
            client=self.client,
            created_by=self.user,
            status='in_progress'
        )
    
    def test_document_number_generation(self):
        """测试文档编号自动生成"""
        doc1 = ProjectArchiveDocument(
            document_name='测试文档1',
            document_type='project_doc',
            project=self.project,
            file_name='test1.pdf',
            file_size=1024,
            uploaded_by=self.user
        )
        doc1.save()
        
        doc2 = ProjectArchiveDocument(
            document_name='测试文档2',
            document_type='project_doc',
            project=self.project,
            file_name='test2.pdf',
            file_size=2048,
            uploaded_by=self.user
        )
        doc2.save()
        
        self.assertIsNotNone(doc1.document_number)
        self.assertIsNotNone(doc2.document_number)
        self.assertNotEqual(doc1.document_number, doc2.document_number)


class ArchiveProjectArchiveTestCase(TestCase):
    """项目归档测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client.objects.create(
            name='测试客户',
            created_by=self.user
        )
        self.project = Project.objects.create(
            project_number='VIH-2024-001',
            project_name='测试项目',
            client=self.client,
            created_by=self.user,
            status='completed'
        )
    
    def test_archive_number_generation(self):
        """测试归档编号自动生成"""
        archive = ArchiveProjectArchive.objects.create(
            project=self.project,
            archive_reason='测试归档',
            applicant=self.user
        )
        self.assertIsNotNone(archive.archive_number)
        self.assertTrue(archive.archive_number.startswith('ARCH-PROJ-'))


class ArchiveBorrowTestCase(TestCase):
    """档案借阅测试"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client = Client.objects.create(
            name='测试客户',
            created_by=self.user
        )
        self.project = Project.objects.create(
            project_number='VIH-2024-001',
            project_name='测试项目',
            client=self.client,
            created_by=self.user,
            status='in_progress'
        )
        self.document = ProjectArchiveDocument.objects.create(
            document_name='测试文档',
            document_type='project_doc',
            project=self.project,
            file_name='test.pdf',
            file_size=1024,
            uploaded_by=self.user,
            status='archived'
        )
    
    def test_borrow_number_generation(self):
        """测试借阅单号自动生成"""
        borrow = ArchiveBorrow.objects.create(
            project_document=self.document,
            borrow_reason='测试借阅',
            borrow_date=timezone.now().date(),
            return_date=timezone.now().date(),
            borrower=self.user
        )
        self.assertIsNotNone(borrow.borrow_number)
        self.assertTrue(borrow.borrow_number.startswith('BOR-'))
    
    def test_borrow_overdue_check(self):
        """测试借阅逾期检查"""
        from datetime import timedelta
        
        borrow = ArchiveBorrow.objects.create(
            project_document=self.document,
            borrow_reason='测试借阅',
            borrow_date=timezone.now().date() - timedelta(days=10),
            return_date=timezone.now().date() - timedelta(days=5),
            borrower=self.user,
            status='out'
        )
        
        self.assertTrue(borrow.is_overdue)

