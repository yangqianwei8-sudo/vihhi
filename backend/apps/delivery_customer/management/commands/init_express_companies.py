"""
初始化快递公司数据的Django管理命令

使用方法：
python manage.py init_express_companies
"""

from django.core.management.base import BaseCommand
from backend.apps.delivery_customer.models import ExpressCompany


class Command(BaseCommand):
    help = '初始化快递公司数据（常见快递公司的全称）'

    def handle(self, *args, **options):
        # 常见快递公司列表（包含全称）
        express_companies = [
            {
                'name': '顺丰速运',
                'code': 'SF',
                'alias': '顺丰,SF,顺丰快递',
                'contact_phone': '95338',
                'website': 'https://www.sf-express.com',
                'sort_order': 1,
                'is_default': True,
            },
            {
                'name': '中国邮政速递物流',
                'code': 'EMS',
                'alias': 'EMS,中国邮政,邮政,邮政速递',
                'contact_phone': '11183',
                'website': 'http://www.ems.com.cn',
                'sort_order': 2,
            },
            {
                'name': '圆通速递',
                'code': 'YTO',
                'alias': '圆通,圆通快递,YTO',
                'contact_phone': '95554',
                'website': 'http://www.yto.net.cn',
                'sort_order': 3,
            },
            {
                'name': '申通快递',
                'code': 'STO',
                'alias': '申通,申通快递,STO',
                'contact_phone': '95543',
                'website': 'http://www.sto.cn',
                'sort_order': 4,
            },
            {
                'name': '中通快递',
                'code': 'ZTO',
                'alias': '中通,中通快递,ZTO',
                'contact_phone': '95311',
                'website': 'http://www.zto.com',
                'sort_order': 5,
            },
            {
                'name': '韵达速递',
                'code': 'YD',
                'alias': '韵达,韵达快递,韵达速递,YD',
                'contact_phone': '95546',
                'website': 'http://www.yundaex.com',
                'sort_order': 6,
            },
            {
                'name': '百世快递',
                'code': 'HTKY',
                'alias': '百世,百世快递,百世汇通,HTKY',
                'contact_phone': '95320',
                'website': 'http://www.800best.com',
                'sort_order': 7,
            },
            {
                'name': '德邦快递',
                'code': 'DBL',
                'alias': '德邦,德邦快递,德邦物流,DBL',
                'contact_phone': '95353',
                'website': 'http://www.deppon.com',
                'sort_order': 8,
            },
            {
                'name': '京东物流',
                'code': 'JD',
                'alias': '京东,京东快递,京东物流,JD',
                'contact_phone': '950616',
                'website': 'https://www.jdwl.com',
                'sort_order': 9,
            },
            {
                'name': '极兔速递',
                'code': 'J&T',
                'alias': '极兔,极兔快递,极兔速递,J&T,JT',
                'contact_phone': '956025',
                'website': 'http://www.jtexpress.com',
                'sort_order': 10,
            },
            {
                'name': '菜鸟裹裹',
                'code': 'CN',
                'alias': '菜鸟,菜鸟裹裹,菜鸟网络,CN',
                'contact_phone': '400-901-0101',
                'website': 'https://www.cainiao.com',
                'sort_order': 11,
            },
            {
                'name': '跨越速运',
                'code': 'KYE',
                'alias': '跨越,跨越速运,跨越物流,KYE',
                'contact_phone': '95324',
                'website': 'http://www.ky-express.com',
                'sort_order': 12,
            },
            {
                'name': '天天快递',
                'code': 'TTKDEX',
                'alias': '天天,天天快递,TTKDEX',
                'contact_phone': '400-188-8888',
                'website': 'http://www.ttkdex.com',
                'sort_order': 13,
            },
            {
                'name': '宅急送',
                'code': 'ZJS',
                'alias': '宅急送,ZJS',
                'contact_phone': '400-6789-000',
                'website': 'http://www.zjs.com.cn',
                'sort_order': 14,
            },
            {
                'name': '联邦快递',
                'code': 'FEDEX',
                'alias': '联邦,联邦快递,FedEx,FEDEX',
                'contact_phone': '400-886-1888',
                'website': 'http://www.fedex.com/cn',
                'sort_order': 15,
            },
            {
                'name': 'DHL快递',
                'code': 'DHL',
                'alias': 'DHL,DHL快递,DHL国际快递',
                'contact_phone': '95380',
                'website': 'https://www.dhl.com/cn-zh',
                'sort_order': 16,
            },
            {
                'name': 'UPS快递',
                'code': 'UPS',
                'alias': 'UPS,UPS快递,UPS国际快递',
                'contact_phone': '400-820-8388',
                'website': 'http://www.ups.com/cn',
                'sort_order': 17,
            },
            {
                'name': 'TNT快递',
                'code': 'TNT',
                'alias': 'TNT,TNT快递,TNT国际快递',
                'contact_phone': '400-820-9868',
                'website': 'http://www.tnt.com/cn',
                'sort_order': 18,
            },
        ]

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for company_data in express_companies:
            name = company_data.pop('name')
            company, created = ExpressCompany.objects.update_or_create(
                name=name,
                defaults=company_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'✓ 创建快递公司: {name}'))
            else:
                updated_count += 1
                self.stdout.write(self.style.WARNING(f'↻ 更新快递公司: {name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n完成！创建: {created_count} 个, 更新: {updated_count} 个'
        ))

