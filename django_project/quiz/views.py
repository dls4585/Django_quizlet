from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from .models import Quiz, Card, login, search_time, download_time, make_time
from json import dumps
from django.utils import timezone
from nltk.tokenize import word_tokenize
import nltk
from konlpy.tag import Okt
from gensim.models.word2vec import Word2Vec
import datetime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os

def get_card(request, pk):
    try:
        card = get_object_or_404(Card, pk=pk)
        card_info = card.values()
        card_info["pk"] = card.pk
        card_info["title"] = card.title
        card_info["description"] = card.description
        return HttpResponse(dumps(card_info), content_type='application/json')
    except:
        return HttpResponse('no')

def get_quizzes(request, pk):
    quiz_list = []
    for quiz_info in Quiz.objects.filter(card=Card.objects.get_by_natural_key(pk)).order_by('order'):
        info = dict()
        info["pk"] = quiz_info.pk
        info["question"] = quiz_info.question
        info["answer"] = quiz_info.answer
        quiz_list.append(info)
    result = dict()
    result['quiz_list'] = quiz_list
    return HttpResponse(dumps(result), content_type='application/json')

def like_card(request, pk, do_or_undo):
    try:
        card = get_object_or_404(Card, pk=pk)
        card.likes += do_or_undo
        card.save()
        card_info = card.values()
        return HttpResponse(dumps(card_info), content_type='application/json')
    except:
        return HttpResponse('no')

def upload_card(request, pk, title, description):
    try:
        card = get_object_or_404(Card, pk=pk)
        card.title = title
        card.description = description
        card.save()
        return HttpResponse(card.pk)
    except:
        return HttpResponse('no')

def upload_quiz(request, pk, question, answer):
    try:
        quiz = get_object_or_404(Quiz, pk=pk)
        quiz.question = question
        quiz.answer = answer
        quiz.save()
        return HttpResponse('ok')
    except:
        return HttpResponse('no')

def save_kw_time(strings):
    kwlist = strings.split()
    for kw in kwlist:
        search_time(keyword=kw, time=timezone.now()).save()

def login_check(name):
    login(user_name=name, time=timezone.now()).save()

def save_down(title):
    download_time(card_title=title, time=timezone.now()).save()

def save_make(title):
    make_time(card_title=title, time=timezone.now()).save()

def search(request, card_name):
    save_kw_time(card_name)
    correspond = Card.objects.filter(title=card_name).order_by('likes').values('id', 'title')
    contained = Card.objects.filter(title__icontains=card_name).exclude(title=card_name).order_by('likes').values('id', 'title')
    #나머지
    related = Card.objects.exclude(title_icontains=card_name).order_by('likes').values('id', 'title')

    result = list() # json 딕셔너리를 담을 list
    b = correspond.union(contained)
    for i in b:
        result.append(i)

    sentence = list()
    if isKorean(card_name) is True:
        #한글 토큰화
        okt = Okt()
        for i in related:
            i['title'] = okt.morphs(i['title'])
            sentence.append(i['title'])
    else:
        #영어 토큰화
        nltk.download('punkt')
        word_tokenize(card_name)
        for i in related:
            i['title'] = word_tokenize(i['title'])
            sentence.append(i['title'])

    #rtn의 개수만큼 for문으로 append하자
    rtn = find_similar(card_name, sentence, skip_gram=True)

    for i in rtn:
        a = Card.objects.filter(title__icontains=i).exclude(title__icontains=card_name).order_by('likes').values()
        for j in a:
            result.append(j)

    return HttpResponse(dumps(result), content_type='application/json')

def isKorean(search):
    k_count = 0
    e_count = 0
    for c in search:
        if ord('가') <= ord(c) <= ord('힣'):
            k_count+=1
        elif ord('a') <= ord(c.lower()) <= ord('z'):
            e_count+=1
    return True if k_count>1 else False

def find_similar(card_name, sentence, skip_gram=True):
    if skip_gram:
        model = Word2Vec(sentence, min_count=10, iter=20, size=100, sg=1)
    else:
        model = Word2Vec(sentence, min_count=10, iter=20, size=100, sg=0)

    model.init_sims(replace=True)
    result = model.wv.most_similar(card_name) #(단어, 유사도) 식으로 표현된 tuple 을 묶은 list
    similar = list()
    for i in result:
        similar.append(i[0])

    return similar


# ------------------------------------------------------------------------------------------
# url

def show(request):
    return render(request, 'period/search.html')


def period_search(request):

    if request.method == 'GET':
        from_time = request.GET.get('from')
        from_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
        to_time = request.GET.get('to')
        to_time = datetime.datetime.strptime(to_time, '%Y-%m-%d')
#        to_time 까지 결과에 포함하기 위해 하루 증가시킴
        to_time = to_time + datetime.timedelta(days=1)

        if request.GET.get('category') == 'keywords':
            data_sr, timelist = make_chart_data(search_time, from_time, to_time)
        elif request.GET.get('category') == 'downloads':
            data_sr, timelist = make_chart_data(download_time, from_time, to_time)
        elif request.GET.get('category') == 'make':
            data_sr, timelist = make_chart_data(make_time, from_time, to_time)
        category = request.GET.get('category')
        contents = {}
        for date in timelist:
            date = date.replace("\n", "", 5)
            contents[date] = date

        make_chart(data_sr)
        return render(request, 'period/graph1.html', {'contents': contents, 'category': category})


def make_chart_data(category, from_time, to_time):
    data = []
    seg_time = from_time + datetime.timedelta(hours=3)
    dates = []
    counts = []
    while from_time < to_time:
        key = x_axis(from_time, seg_time)
        dates.append(from_time)
        count = category.objects.filter(time__gte=from_time).exclude(time__gt=seg_time).count()
        data.append(key)
        counts.append(count)
        from_time = from_time + datetime.timedelta(hours=3)
        seg_time = seg_time + datetime.timedelta(hours=3)
        if seg_time > to_time:
            seg_time = to_time
    data_sr = pd.Series(counts, index=dates)
    return data_sr, data


def x_axis(from_time, seg_time):
    key = datetime.datetime.strftime(from_time, '%Y-%m-%d %H:%M')
    key2 = datetime.datetime.strftime(seg_time, '%Y-%m-%d %H:%M')
    key = key + '\n' + ' ~ ' + key2
    return key


def make_chart(data_sr):

    plt.figure(figsize=(11, 7))
    plt.bar(data_sr.index, data_sr.values, width=0.1)
    plt.xlabel('Period')
    plt.ylabel('Search')
    plt.xticks(fontsize=7)
    plt.tight_layout()
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'quiz/static')
    file_path = os.path.join(base_dir, 'images/graph/foo.png').replace("\\", "/", 30)

    plt.savefig(file_path)

# ----------------------------------------------------

def show_result(request):
    category = request.GET.get('category')
    get_data = request.GET.get('period').split(" ~ ")
    contents = request.GET.get('contents')
    from_time = datetime.datetime.strptime(get_data[0], "%Y-%m-%d %H:%M")
    to_time = datetime.datetime.strptime(get_data[1], "%Y-%m-%d %H:%M") + datetime.timedelta(minutes=1)
    name_list = []
    count = {}
    if request.GET.get('category') == 'keywords':
        data = search_time.objects.filter(time__gte=from_time).exclude(time__gt=to_time).values('keyword', 'time')
        key = 'keyword'
    elif request.GET.get('category') == 'downloads':
        data = download_time.objects.filter(time__gte=from_time).exclude(time__gt=to_time).values('card_name', 'time')
        key = 'card_name'
    elif request.GET.get('category') == 'make':
        data = make_time.objects.filter(time__gte=from_time).exclude(time__gt=to_time).values('card_name', 'time')
        key = 'card_name'
    add_list(data, key, name_list)
    count_repetition(count, name_list)
    name = []
    number = []
    sort = sorted(count.items(), key=lambda item: item[1], reverse=True)
    for i in sort:
        name.append(i[0])
        number.append(i[1])
    data_sr = pd.Series(number, index=name)
    make_chart2(data_sr, key)
    return render(request, 'period/graph2.html', {'contents': contents, 'category': category})

def add_list(data, key, name_list):
    for i in data:
        name_list.append(i[key])


def count_repetition(count, name_list):
    lists=[]
    for i in name_list:
        try: count[i] += 1
        except: count[i] = 1

# 그래프 세부 조정 하기
def make_chart2(data_sr, key):
    font_path = "C:\\Windows\\Fonts\\gulim.ttc".replace("\\", "/", 10)
    font_name = fm.FontProperties(fname=font_path, size=100).get_name()
    plt.rc('font', family=font_name)

    plt.figure(figsize=(11, 7))
    plt.barh(data_sr.index, data_sr.values, height=0.1)
    plt.xlabel(key)
    plt.ylabel('amount')
    plt.xticks(fontsize=7)
    plt.tight_layout()
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'quiz/static')
    file_path = os.path.join(base_dir, 'images/graph/poo.png').replace("\\", "/", 30)

    plt.savefig(file_path)

##개선사항 : 그래프 세부조정 / 두번째 그래프 띄우고 나서 폼 계속 띄우기 (search2 -> result html 전환 문제)