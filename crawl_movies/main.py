from google.cloud import storage
from config import CONFIG
import requests
from bs4 import BeautifulSoup
import ujson as json
import traceback


BASIC_URL = "https://movie.naver.com/movie/bi/mi/basic.nhn?code=%d"
DETAIL_URL = "https://movie.naver.com/movie/bi/mi/detail.nhn?code=%d"


def crawl_movie(request):
    r = request.get_json()
    movie_code = r['code']

    movie_dict = {}
    res = requests.get(BASIC_URL % movie_code)
    b = BeautifulSoup(res.text, 'lxml')

    try:
        movie_info = b.find('div', {'class': 'mv_info'})
        movie_dict['name'] = " ".join(movie_info.find('h3', 'h_movie').find('a').text.split())
    except:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_type': 'movie not exist'
        }
        return json.dumps(result)

    try:
        score = movie_info.find('div', {'class': 'main_score'})
        score = score.find('a', {'id': 'pointNetizenPersentWide'})
        span = score.find('span')
        if span is not None:
            span.extract()
        score = float(score.text.strip())
        assert score != 0.0 # remove movies with score zero
        movie_dict['netizen_score'] = score
    except:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_type': 'movie score not exist'
        }
        return json.dumps(result)

    try:
        movie_info = b.find('dl', {'class': 'info_spec'})
        info_list = movie_info.findAll('dd')
        movie_info_sub = info_list[0].findAll('span')

        movie_dict['categories'] = "".join(movie_info_sub[0].text.split())
        movie_dict['countries'] = "".join(movie_info_sub[1].text.split())
        movie_dict['runtime'] = " ".join(movie_info_sub[2].text.split())
        movie_dict['class'] = info_list[-2].find('a').text.strip()
    except:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_type': 'movie info not enough'
        }
        return json.dumps(result)

    try:
        story = b.find('div', {'class': 'story_area'})
        # remove "줄거리"
        story_title = story.find('div', {'class': 'title_area'})
        if story_title is not None:
            story_title.extract()
        movie_dict['story'] = " ".join(story.text.split())
    except:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_type': 'movie story not exist'
        }
        return json.dumps(result)

    res = requests.get(DETAIL_URL % movie_code)
    b = BeautifulSoup(res.text, 'lxml')

    movie_dict['actors'] = []
    try:
        actors = b.find('ul', {'class': 'lst_people'}).findAll('div', {'class': 'p_info'})
        assert len(actors) > 0
    except:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_type': 'cannot find actors'
        }
        return json.dumps(result)

    for actor in actors:
        try:
            actor_a = actor.find('a', {'class': 'k_name'})
            code = actor_a['href'].split('=')[1]
            name = " ".join(actor_a.text.split())
            part = actor.find('em', {'class': 'p_part'}).text.split()
            movie_dict['actors'].append({'code': code, 'name': name, 'part': part})
        except TypeError:
            continue

    movie_dict['directors'] = []
    try:
        directors = b.find('div', {'class': 'director'}).findAll('div', {'class': 'dir_obj'})
        assert len(directors) > 0
    except:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_type': 'cannot find directors'
        }
        return json.dumps(result)
    
    for director in directors:
        try:
            director_a = director.find('a', {'class': 'k_name'})
            code = director_a['href'].split('=')[1]
            name = " ".join(actor_a.text.split())
            movie_dict['directors'].append({'code': code, 'name': name})
        except TypeError:
            continue

    # save info into storage
    try:
        storage.Client()
        client = storage.Client(project=CONFIG['PROJECT_NAME'])
        bucket = client.get_bucket(CONFIG['CLOUD_STORAGE_BUCKET'])
        blob = bucket.blob(f'movie_{movie_code}.json')
        blob.upload_from_string(json.dumps(movie_dict))
    except Exception:
        result = {
            'status': False, 
            'code': movie_code, 
            'e_msg': traceback.format_exc(),
            'e_type': 'saving fail'
        }
        return  json.dumps(result)
    
    result = {'status': True, 'code': movie_code}
    return json.dumps(result)
