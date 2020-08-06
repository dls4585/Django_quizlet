from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from scipy.sparse.data import _data_matrix
from .models import Quiz, Card, Login, Search_time, Download_time, Make_time
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
from dateutil.relativedelta import relativedelta
import numpy as np

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
        Search_time(keyword=kw, time=timezone.now()).save()

def login_check(name):
    Login(user_name=name, time=timezone.now()).save()

def save_down(title):
    Download_time(card_title=title, time=timezone.now()).save()

def save_make(title):
    Make_time(card_title=title, time=timezone.now()).save()

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
# 관리자페이지


def main(request):
    total_login = Login.objects.count()
    today = datetime.date.today()
    today_login = Login.objects.filter(time__gte=today).count()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_login = Login.objects.filter(time__gte=yesterday).count() - today_login

    most_cards = Card.objects.order_by('-likes')[:5]

    plt.figure(figsize=(5, 5))
    x = [-7, -6, -5, -4, -3, -2, -1]
    y = []
    for i in range(7):
        bd1 = datetime.date.today() - datetime.timedelta(days=7-i)
        bd2 = datetime.date.today() - datetime.timedelta(days=6-i)
        bd_cnt1 = Login.objects.filter(time__gte=bd1).count()
        bd_cnt2 = Login.objects.filter(time__gte=bd2).count()
        y.append(bd_cnt1 - bd_cnt2)

    plt.bar(x, y)
    plt.xlabel('요일')
    plt.ylabel('방문자 수')
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'quiz/static')
    file_path = os.path.join(base_dir, 'images/graph/qaz.png').replace("\\", "/", 30)

    plt.savefig(file_path)

    return render(request, 'main.html', {'total_login': total_login,
                                         'today_login': today_login,
                                         'yesterday_login': yesterday_login,
                                         'most_cards': most_cards})

#---------------------------------------

def show_default_graph(request):
    today_date = datetime.datetime.today().date()
    today_str = today_date.strftime("%Y-%m-%d")
    df, title = make_hourly_df_and_title(today_str, today_str)
    title = "Today : " + today_str
    draw_graph(df, title)
    return render(request, 'quiz/visitors.html')


def show_num_of_visitors(request):
    scale = request.GET.get('scale')
    from_time = request.GET.get('from')
    to_time = request.GET.get('to')

    if scale == 'time':
        df, title = make_hourly_df_and_title(from_time, to_time)
        draw_graph(df, title)
    elif scale == 'day':
        df, title = make_daily_df_and_title(from_time, to_time)
        draw_graph(df, title)
    elif scale == 'week':
        df, title = make_weekly_df_and_title(from_time, to_time)
        draw_graph(df, title)
    elif scale == 'month':
        df, title = make_monthly_df_and_title(from_time, to_time)
        draw_graph(df, title)

    return render(request, 'quiz/visitors_results.html')


def make_hourly_df_and_title(from_time, to_time):
    start_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
    start_time_copy = start_time
    end_time = datetime.datetime.strptime(to_time, '%Y-%m-%d') + datetime.timedelta(days=1)

    ####################################
    hour_list = []
    while True:
        if end_time < start_time:
            break
        hour_list.append(start_time)
        start_time = start_time + datetime.timedelta(hours=1)

    num_of_visitors = [0 for i in range(len(hour_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=hour_list)

    login_list = Login.objects.filter(time__range=[start_time_copy, end_time])
    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        visitors_df[login_time_floored] += 1

    title = "Hourly : " + from_time + " ~ " + to_time
    return visitors_df, title


def make_daily_df_and_title(from_time, to_time):
    start_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
    start_time_copy = start_time
    end_time = datetime.datetime.strptime(to_time, '%Y-%m-%d') + datetime.timedelta(days=1)

    ####################################
    day_list = []
    while True:
        if end_time < start_time:
            break
        day_list.append(start_time)
        start_time = start_time + datetime.timedelta(days=1)

    num_of_visitors = [0 for i in range(len(day_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=day_list)

    login_list = Login.objects.filter(time__range=[start_time_copy, end_time])
    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(hours=i.time.hour, minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        visitors_df[login_time_floored] += 1
    visitors_df = visitors_df.drop(day_list[-1])

    title = "Dailly : " + from_time + " ~ " + to_time
    return visitors_df, title


def make_weekly_df_and_title(from_time, to_time):
    start_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
    end_time = datetime.datetime.strptime(to_time, '%Y-%m-%d') + datetime.timedelta(days=1)

    start_time_weekday = start_time.weekday()
    end_time_weekday = end_time.weekday()
    if end_time_weekday - start_time_weekday >= 0:
        delta = 7 - (end_time_weekday - start_time_weekday)
        start_time = start_time - datetime.timedelta(days=delta)
    else:
        delta = end_time_weekday - start_time_weekday
        start_time = start_time + datetime.timedelta(days=delta)
    start_time_copy = start_time

    ####################################
    week_list = []
    while True:
        if end_time < start_time:
            break
        week_list.append(start_time)
        start_time = start_time + datetime.timedelta(weeks=1)

    num_of_visitors = [0 for i in range(len(week_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=week_list)
    login_list = Login.objects.filter(time__range=[start_time_copy, end_time])

    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(hours=i.time.hour, minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        weekday_delta = login_time_floored.weekday() - start_time_copy.weekday()
        if weekday_delta < 0:
            weekday_delta = weekday_delta + 7
        login_time_floored = login_time_floored - datetime.timedelta(days = weekday_delta)
        visitors_df[login_time_floored] += 1
    visitors_df = visitors_df.drop(week_list[-1])

    title = "Weekly : " + start_time_copy.strftime("%Y-%m-%d") + " ~ " + to_time
    return visitors_df, title


def make_monthly_df_and_title(from_time, to_time):
    from_time = from_time[:7]
    to_time = to_time[:7]
    start_time = datetime.datetime.strptime(from_time, '%Y-%m')
    start_time_copy = start_time
    end_time = datetime.datetime.strptime(to_time, '%Y-%m') + relativedelta(months=1)

    ####################################
    month_list = []

    while True:
        if end_time < start_time:
            break
        month_list.append(start_time)
        start_time = start_time + relativedelta(months=1)

    print(month_list, "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    num_of_visitors = [0 for i in range(len(month_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=month_list)

    login_list = Login.objects.filter(time__range=[start_time_copy, end_time])
    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(days=i.time.day-1, hours=i.time.hour, minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        visitors_df[login_time_floored] += 1
    visitors_df = visitors_df.drop(month_list[-1])

    title = "Monthly : " + from_time + " ~ " + to_time
    return visitors_df, title


def draw_graph(dataframe, title):
    plt.figure(figsize=(11, 5))
    plt.title(title)
    plt.yticks(np.arange(0, max(dataframe.values)+1, 1))
    plt.stem(dataframe.index, dataframe.values)
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'quiz/static')
    file_path = os.path.join(base_dir, 'images/graph/foo.png').replace("\\", "/", 30)

    plt.savefig(file_path)

def show_card_list(request):
    card_list = Card.objects.all().order_by('-likes')
    context = {'cards': card_list}
    print(card_list)
    return render(request, 'quiz/cards.html', context)


def show_card_list_searched(request):
    keyword = request.GET.get('keyword')
    card_list = Card.objects.filter(title__contains=keyword).order_by('-likes')
    context = {'cards': card_list}
    return render(request, 'quiz/cards.html', context)


def retrive_card(request):
    pk = request.GET.get('pk')
    target_card = Card.objects.filter(pk=pk)[0]
    context = {'card' : target_card}
    return render(request, 'quiz/card_retrieved.html', context)


#---------------------------------------

def basic_search_view(request):
    return render(request, 'period/search.html')


def graph_for_category_view(request):

    if request.method == 'GET':
        from_time = request.GET.get('from')
        from_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
        to_time = request.GET.get('to')
        to_time = datetime.datetime.strptime(to_time, '%Y-%m-%d')
#        to_time 까지 결과에 포함하기 위해 하루 증가시킴
        to_time = to_time + datetime.timedelta(days=1)

        if request.GET.get('category') == 'keywords':
            data_sr, timelist = make_chart_data(Search_time, from_time, to_time)
        elif request.GET.get('category') == 'downloads':
            data_sr, timelist = make_chart_data(Download_time, from_time, to_time)
        elif request.GET.get('category') == 'make':
            data_sr, timelist = make_chart_data(Make_time, from_time, to_time)
        category = request.GET.get('category')
        time_options = {}
        for date in timelist:
            date = date.replace("\n", "", 5)
            time_options[date] = date

        make_chart(data_sr)
        return render(request, 'period/graph1.html', {'time_options': time_options, 'category': category})


def make_chart_data(category, from_time, to_time):
    seg_time = from_time + datetime.timedelta(hours=3)
    timelist = []
    index_dates = []
    column_counts = []
    while from_time < to_time:
        x_key = x_axis(from_time, seg_time)
        index_dates.append(from_time)
        count = category.objects.filter(time__gte=from_time).exclude(time__gt=seg_time).count()
        timelist.append(x_key)
        column_counts.append(count)
        from_time = from_time + datetime.timedelta(hours=3)
        seg_time = seg_time + datetime.timedelta(hours=3)
        if seg_time > to_time:
            seg_time = to_time
    data_sr = pd.Series(column_counts, index=index_dates)
    return data_sr, timelist


def x_axis(from_time, seg_time):
    key = datetime.datetime.strftime(from_time, '%Y-%m-%d %H:%M')
    key2 = datetime.datetime.strftime(seg_time, '%Y-%m-%d %H:%M')
    key = key + '\n' + ' ~ ' + key2
    return key


def make_chart(data_sr):
    plt.figure(figsize=(11, 6))
    plt.bar(data_sr.index, data_sr.values, width=0.1)
    plt.xlabel('Period')
    plt.ylabel('Search')
    plt.xticks(fontsize=7)
    plt.tight_layout()
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'quiz/static')
    file_path = os.path.join(base_dir, 'images/graph/goo.png').replace("\\", "/", 30)

    plt.savefig(file_path)

# ----------------------------------------------------

def graph_detail_view(request):
    category = request.GET.get('category')
    data_from_html = request.GET.get('period').split(" ~ ")
    time_options = request.GET.get('time_options')
    from_time = datetime.datetime.strptime(data_from_html[0], "%Y-%m-%d %H:%M")
    to_time = datetime.datetime.strptime(data_from_html[1], "%Y-%m-%d %H:%M") + datetime.timedelta(minutes=1)
    name_list = []
    counts = {}
    if request.GET.get('category') == 'keywords':
        data = Search_time.objects.filter(time__gte=from_time).exclude(time__gt=to_time).values('keyword', 'time')
        field = 'keyword'
    elif request.GET.get('category') == 'downloads':
        data = Download_time.objects.filter(time__gte=from_time).exclude(time__gt=to_time).values('card_name', 'time')
        field = 'card_name'
    elif request.GET.get('category') == 'make':
        data = Make_time.objects.filter(time__gte=from_time).exclude(time__gt=to_time).values('card_name', 'time')
        field = 'card_name'
    add_list(data, field, name_list)
    count_repetition(counts, name_list)
    index_name = []
    column_counts = []
    sort_counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    for i in sort_counts:
        index_name.append(i[0])
        column_counts.append(i[1])
    data_sr = pd.Series(column_counts, index=index_name)
    make_detail_chart(data_sr, field)
    return render(request, 'period/graph2.html', {'time_options': time_options, 'category': category})

def add_list(data, field, name_list):
    for i in data:
        name_list.append(i[field])


def count_repetition(count, name_list):
    lists=[]
    for i in name_list:
        try: count[i] += 1
        except: count[i] = 1

# 그래프 세부 조정 하기
def make_detail_chart(data_sr, field):
    font_path = "C:\\Windows\\Fonts\\gulim.ttc".replace("\\", "/", 10)
    font_name = fm.FontProperties(fname=font_path, size=100).get_name()
    plt.rc('font', family=font_name)

    plt.figure(figsize=(11, 6))
    plt.barh(data_sr.index, data_sr.values, height=0.1)

    plt.xlabel(field)
    plt.ylabel('amount')
    plt.xticks(fontsize=7)
    plt.tight_layout()
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            'quiz/static')
    file_path = os.path.join(base_dir, 'images/graph/poo.png').replace("\\", "/", 30)

    plt.savefig(file_path)

##개선사항 : 그래프 세부조정 / 두번째 그래프 띄우고 나서 폼 계속 띄우기 (search2 -> result html 전환 문제)