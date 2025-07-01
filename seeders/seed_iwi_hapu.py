import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'iwi_web_app.settings')
    django.setup()
    from core.models import Iwi, Hapu

    iwi_data = [
        {'name': 'Ngāpuhi', 'description': 'Largest iwi in New Zealand.'},
        {'name': 'Ngāti Porou', 'description': 'East Coast iwi.'},
        {'name': 'Waikato-Tainui', 'description': 'Based in the Waikato region.'},
    ]

    hapu_data = [
        {'iwi': 'Ngāpuhi', 'name': 'Ngāti Hine', 'description': 'A prominent hapū of Ngāpuhi.'},
        {'iwi': 'Ngāpuhi', 'name': 'Te Uri Taniwha', 'description': ''},
        {'iwi': 'Ngāti Porou', 'name': 'Te Whānau a Apanui', 'description': ''},
        {'iwi': 'Waikato-Tainui', 'name': 'Ngāti Mahuta', 'description': ''},
    ]

    iwi_objs = {}
    for iwi in iwi_data:
        obj, _ = Iwi.objects.get_or_create(name=iwi['name'], defaults={'description': iwi['description']}) # type: ignore
        iwi_objs[iwi['name']] = obj

    for hapu in hapu_data:
        iwi_obj = iwi_objs.get(hapu['iwi'])
        if iwi_obj:
            Hapu.objects.get_or_create( # type: ignore
                iwi=iwi_obj,
                name=hapu['name'],
                defaults={'description': hapu['description']}
            )

    print('Iwi and Hapu seeded successfully.')

if __name__ == '__main__':
    main() 