from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from scipy.sparse.data import _data_matrix
from .models import Quiz, Card, Login, Search_time, Download_time, Make_time
from json import dumps
from django.utils import timezone
from .forms import *
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
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import csv
from django.contrib import messages

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

def delete_quiz(pk):
    for quiz in Quiz.objects.filter(card=Card.objects.get(pk=pk)):
        quiz.delete()


def delete_card(request, pk):
    card = get_object_or_404(Card, pk=pk)
    card.delete()
    return HttpResponse("ok")

def save_kw_time(strings):
    kwlist = strings.split()
    for kw in kwlist:
        Search_time(keyword=kw, time=timezone.now()).save()

def login_check(name):
    Login(user_name=name, time=timezone.now()).save()

def save_down(title, pk):
    Download_time(card_title=title, time=timezone.now(), card=Card.objects.get_by_natural_key(pk)).save()

def save_make(title):
    Make_time(card_title=title, time=timezone.now()).save()

def search(request, card_name):
    save_kw_time(card_name)
    correspond = Card.objects.filter(title=card_name).order_by('-likes')
    contained = Card.objects.filter(title__icontains=card_name).exclude(title=card_name).order_by('-likes')
    description_search = Card.objects.filter(description__icontains=card_name)\
        .exclude(title__icontains=card_name).order_by('-likes')
    hashtag_search = Card.objects.filter(hashtag__icontains=card_name).\
        exclude(title__icontains=card_name).exclude(description__icontains=card_name).order_by('-likes')
    #나머지
    related = Card.objects.exclude(title__icontains=card_name).exclude(description__icontains=card_name).exclude(hashtag__icontains=card_name)

    result = list() # json 딕셔너리를 담을 list
    for i in correspond:
        if i in result:
            continue
        else:
            result.append(i)
    for i in contained:
        if i in result:
            continue
        else:
            result.append(i)
    for i in description_search:
        if i in result:
            continue
        else:
            result.append(i)
    for i in hashtag_search:
        if i in result:
            continue
        else:
            result.append(i)

    sentence = list()
    if isKorean(card_name) is True:
        #한글 토큰화
        okt = Okt()
        for i in related:
            if isKorean(i.title) is True:
                sentence.append(okt.morphs(i.title))
            else:
                sentence.append(word_tokenize(i.title))
    else:
        #영어 토큰화
        nltk.download('punkt')
        word_tokenize(card_name)
        for i in related:
            if isKorean(i.title) is False:
                sentence.append(word_tokenize(i.title))
            else:
                sentence.append(word_tokenize(i.title))
    #rtn의 개수만큼 for문으로 append하자
    try:
        rtn = find_similar(card_name, sentence, skip_gram=True)
    except:
        return HttpResponse(dumps(result), content_type='application/json')

    for i in rtn:
        a = Card.objects.filter(title__icontains=i).exclude(title__icontains=card_name).order_by('-likes').values()
        for j in a:
            if j in result:
                continue
            else:
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
        model = Word2Vec(sentence, min_count=1, iter=20, size=100, sg=1)
    else:
        model = Word2Vec(sentence, min_count=1, iter=20, size=100, sg=0)

    model.init_sims(replace=True)
    result = model.wv.most_similar(card_name) #(단어, 유사도) 식으로 표현된 tuple 을 묶은 list
    similar = list()
    for i in result:
        similar.append(i[0])

    return similar

# ------------------------------------------------------------------------------------------
# 관리자페이지

@login_required
def main(request):
    total_login = Login.objects.count()
    today = datetime.date.today()
    today_login = Login.objects.filter(time__gte=today).count()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    yesterday_login = Login.objects.filter(time__gte=yesterday).count() - today_login

    most_cards = Card.objects.order_by('-likes')[:5]

    plt.figure(figsize=(5, 5))
    x = ['월', '화', '수', '목', '금', '토', '일', '월', '화', '수', '목', '금', '토', '일', '월', '화', '수', '목']
    y = []

    dt = datetime.datetime.now().weekday()

    for i in range(7):
        bd1 = datetime.date.today() - datetime.timedelta(days=6-i)
        bd2 = datetime.date.today() - datetime.timedelta(days=5-i)
        bd_cnt1 = Login.objects.filter(time__gte=bd1).count()
        bd_cnt2 = Login.objects.filter(time__gte=bd2).count()
        y.append(bd_cnt1 - bd_cnt2)

    font_path = "C:\\Windows\\Fonts\\gulim.ttc".replace("\\", "/", 10)
    font_name = fm.FontProperties(fname=font_path, size=100).get_name()
    plt.rc('font', family=font_name)

    plt.bar(x[dt+1:dt+8], y)
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
@login_required
def show_default_graph(request):
    today_date = datetime.datetime.today().date()
    today_str = today_date.strftime("%Y-%m-%d")
    df, title = make_hourly_df_and_title(today_str)
    title = "Today : " + today_str
    draw_graph(df, title)
    return render(request, 'quiz/visitors.html')


@login_required
def show_num_of_visitors(request):
    scale = request.GET.get('scale')

    if scale == 'hourly':
        target_date = request.GET.get('date')
        df, title = make_hourly_df_and_title(target_date)
        draw_graph(df, title)
        context = {'scale': scale, 'date': target_date}
        return render(request, 'quiz/visitors_hourly.html', context)
    elif scale == 'daily':
        from_date = request.GET.get('from')
        to_date = request.GET.get('to')
        df, title = make_daily_df_and_title(from_date, to_date)
        draw_graph(df, title)
        context = {'scale': scale, 'from_date': from_date, 'to_date': to_date}
        return render(request, 'quiz/visitors_daily.html', context)
    elif scale == 'weekly':
        from_date = request.GET.get('from')
        to_date = request.GET.get('to')
        df, title = make_weekly_df_and_title(from_date, to_date)
        draw_graph(df, title)
        context = {'scale': scale, 'from_date': from_date, 'to_date': to_date}
        return render(request, 'quiz/visitors_weekly.html', context)
    elif scale == 'monthly':
        from_month = request.GET.get('from')
        to_month = request.GET.get('to')
        df, title = make_monthly_df_and_title(from_month, to_month)
        draw_graph(df, title)
        context = {'scale': scale, 'from_month': from_month, 'to_month': to_month}
        return render(request, 'quiz/visitors_monthly.html', context)


def make_hourly_df_and_title(date):
    start_time = datetime.datetime.strptime(date, '%Y-%m-%d')
    start_time_copy = start_time
    end_time = datetime.datetime.strptime(date, '%Y-%m-%d') + datetime.timedelta(days=1)

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

    title = "Hourly Graph : " + date
    return visitors_df, title


def make_daily_df_and_title(from_date, to_date):
    start_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    start_date_copy = start_date
    end_date= datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)

    ####################################
    day_list = []
    while True:
        if end_date < start_date:
            break
        day_list.append(start_date)
        start_date = start_date + datetime.timedelta(days=1)

    num_of_visitors = [0 for i in range(len(day_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=day_list)
    visitors_df = visitors_df.drop(day_list[-1])

    login_list = Login.objects.filter(time__range=[start_date_copy, end_date])
    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(hours=i.time.hour, minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        visitors_df[login_time_floored] += 1

    title = "Dailly : " + from_date + " ~ " + to_date
    return visitors_df, title


def make_weekly_df_and_title(from_date, to_date):
    start_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)

    start_date_weekday = start_date.weekday()
    end_date_weekday = end_date.weekday()
    if end_date_weekday - start_date_weekday >= 0:
        delta = 7 - (end_date_weekday - start_date_weekday)
        start_date = start_date - datetime.timedelta(days=delta)
    else:
        delta = end_date_weekday - start_date_weekday
        start_date = start_date + datetime.timedelta(days=delta)
    start_date_copy = start_date

    ####################################
    week_list = []
    while True:
        if end_date < start_date:
            break
        week_list.append(start_date)
        start_date = start_date + datetime.timedelta(weeks=1)

    num_of_visitors = [0 for i in range(len(week_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=week_list)
    visitors_df = visitors_df.drop(week_list[-1])

    login_list = Login.objects.filter(time__range=[start_date_copy, end_date])
    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(hours=i.time.hour, minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        weekday_delta = login_time_floored.weekday() - start_date_copy.weekday()
        if weekday_delta < 0:
            weekday_delta = weekday_delta + 7
        login_time_floored = login_time_floored - datetime.timedelta(days = weekday_delta)
        visitors_df[login_time_floored] += 1

    title = "Weekly : " + start_date_copy.strftime("%Y-%m-%d") + " ~ " + to_date
    return visitors_df, title


def make_monthly_df_and_title(from_month, to_month):
    start_month_1 = datetime.datetime.strptime(from_month, '%Y-%m')
    start_month_1_copy = start_month_1
    next_month_of_end_month_1 = datetime.datetime.strptime(to_month, '%Y-%m') + relativedelta(months=1)

    ####################################
    month_list = []

    while True:
        if next_month_of_end_month_1 < start_month_1:
            break
        month_list.append(start_month_1)
        start_month_1 = start_month_1 + relativedelta(months=1)

    num_of_visitors = [0 for i in range(len(month_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=month_list)
    visitors_df = visitors_df.drop(month_list[-1])

    login_list = Login.objects.filter(time__range=[start_month_1_copy, next_month_of_end_month_1])
    for i in login_list:
        login_time_floored = i.time - \
                             datetime.timedelta(days=i.time.day-1, hours=i.time.hour, minutes=i.time.minute, seconds=i.time.second, microseconds=i.time.microsecond)
        visitors_df[login_time_floored] += 1

    title = "Monthly Graph: " + from_month + " ~ " + to_month
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


@login_required
def show_visitors_detail(request):
    scale = request.GET.get('scale')
    if scale == 'daily':
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        from_time = request.GET.get('from_time')
        to_time = request.GET.get('to_time')
        df, title = show_daily_detail(from_date, to_date, from_time, to_time)
        draw_graph(df, title)
        context = {'scale': scale, 'from_date': from_date, 'to_date': to_date}
        return render(request, 'quiz/visitors_daily.html', context)
    elif scale == 'weekly':
        from_date = request.GET.get('from_date')
        to_date = request.GET.get('to_date')
        from_time = request.GET.get('from_time')
        to_time = request.GET.get('to_time')
        df, title = show_weekly_detail(from_date, to_date, from_time, to_time)
        draw_graph(df, title)
        context = {'scale': scale, 'from_date': from_date, 'to_date': to_date}
        return render(request, 'quiz/visitors_weekly.html', context)
    elif scale == 'monthly':
        from_month = request.GET.get('from_month')
        to_month = request.GET.get('to_month')
        from_time = request.GET.get('from_time')
        to_time = request.GET.get('to_time')
        df, title = show_monthly_detail(from_month, to_month, from_time, to_time)
        draw_graph(df, title)
        context = {'scale': scale, 'from_month': from_month, 'to_month': to_month}
        return render(request, 'quiz/visitors_monthly.html', context)


def show_daily_detail(from_date, to_date, from_time, to_time):
    start_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    start_date_copy = start_date
    end_date = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)
    from_time = int(from_time[0:2])
    to_time = int(to_time[0:2])

    ####################################
    day_list = []
    while True:
        if end_date < start_date:
            break
        day_list.append(start_date)
        start_date = start_date + datetime.timedelta(days=1)

    num_of_visitors = [0 for i in range(len(day_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=day_list)
    visitors_df = visitors_df.drop(day_list[-1])

    login_list = Login.objects.filter(time__range=[start_date_copy, end_date])
    refined_login_list = []
    for i in login_list:
        if from_time <= i.time.hour < to_time:
            refined_login_list.append(i)
    for j in refined_login_list:
        login_time_floored = j.time - \
                             datetime.timedelta(hours=j.time.hour, minutes=j.time.minute, seconds=j.time.second, microseconds=j.time.microsecond)
        visitors_df[login_time_floored] += 1

    title = "Dailly : " + from_date + " ~ " + to_date + " from " + str(from_time) + " to " + str(to_time)
    return visitors_df, title


def show_weekly_detail(from_date, to_date, from_time, to_time):
    start_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    end_date = datetime.datetime.strptime(to_date, '%Y-%m-%d') + datetime.timedelta(days=1)
    from_time = int(from_time[0:2])
    to_time = int(to_time[0:2])

    start_date_weekday = start_date.weekday()
    end_date_weekday = end_date.weekday()
    if end_date_weekday - start_date_weekday >= 0:
        delta = 7 - (end_date_weekday - start_date_weekday)
        start_date = start_date - datetime.timedelta(days=delta)
    else:
        delta = end_date_weekday - start_date_weekday
        start_date = start_date + datetime.timedelta(days=delta)
    start_date_copy = start_date

    ####################################
    week_list = []
    while True:
        if end_date < start_date:
            break
        week_list.append(start_date)
        start_date = start_date + datetime.timedelta(weeks=1)

    num_of_visitors = [0 for i in range(len(week_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=week_list)
    visitors_df = visitors_df.drop(week_list[-1])

    login_list = Login.objects.filter(time__range=[start_date_copy, end_date])
    refined_login_list = []
    for i in login_list:
        if from_time <= i.time.hour < to_time:
            refined_login_list.append(i)
    for j in refined_login_list:
        login_time_floored = j.time - \
                             datetime.timedelta(hours=j.time.hour, minutes=j.time.minute, seconds=j.time.second, microseconds=j.time.microsecond)
        weekday_delta = login_time_floored.weekday() - start_date_copy.weekday()
        if weekday_delta < 0:
            weekday_delta = weekday_delta + 7
        login_time_floored = login_time_floored - datetime.timedelta(days=weekday_delta)
        visitors_df[login_time_floored] += 1

    title = "Weekly Graph: " + start_date_copy.strftime("%Y-%m-%d") + " ~ " + to_date + " from " + str(from_time) + " to " + str(to_time)
    return visitors_df, title


def show_monthly_detail(from_month, to_month, from_time, to_time):
    start_month_1 = datetime.datetime.strptime(from_month, '%Y-%m')
    start_month_1_copy = start_month_1
    next_month_of_end_month_1 = datetime.datetime.strptime(to_month, '%Y-%m') + relativedelta(months=1)
    from_time = int(from_time[0:2])
    to_time = int(to_time[0:2])

    ####################################
    month_list = []
    while True:
        if next_month_of_end_month_1 < start_month_1:
            break
        month_list.append(start_month_1)
        start_month_1 = start_month_1 + relativedelta(months=1)

    num_of_visitors = [0 for i in range(len(month_list))]
    visitors_df = pd.Series(data=num_of_visitors, index=month_list)
    visitors_df = visitors_df.drop(month_list[-1])

    login_list = Login.objects.filter(time__range=[start_month_1_copy, next_month_of_end_month_1])
    refined_login_list = []
    for i in login_list:
        if from_time <= i.time.hour < to_time:
            refined_login_list.append(i)
    for j in refined_login_list:
        login_time_floored = j.time - \
                             datetime.timedelta(days=j.time.day-1, hours=j.time.hour, minutes=j.time.minute, seconds=j.time.second, microseconds=j.time.microsecond)
        visitors_df[login_time_floored] += 1

    title = "Monthly Graph: " + from_month + " ~ " + to_month + " from " + str(from_time) + " to " + str(to_time)
    return visitors_df, title

@login_required
def show_card_list(request):
    card_list = Card.objects.all()
    context = {'cards': card_list}
    return render(request, 'quiz/cards.html', context)

@login_required
def show_card_list_searched(request):
    card_name = request.GET.get('keyword')
    save_kw_time(card_name)
    correspond = Card.objects.filter(title=card_name).order_by('-likes')
    contained = Card.objects.filter(title__icontains=card_name).exclude(title=card_name).order_by('-likes')
    description_search = Card.objects.filter(description__icontains=card_name) \
        .exclude(title__icontains=card_name).order_by('-likes')
    hashtag_search = Card.objects.filter(hashtag__icontains=card_name). \
        exclude(title__icontains=card_name).exclude(description__icontains=card_name).order_by('-likes')
    # 나머지
    related = Card.objects.exclude(title__icontains=card_name).exclude(description__icontains=card_name).exclude(
        hashtag__icontains=card_name)

    result = list()  # json 딕셔너리를 담을 list
    for i in correspond:
        if i in result:
            continue
        else:
            result.append(i)
    for i in contained:
        if i in result:
            continue
        else:
            result.append(i)
    for i in description_search:
        if i in result:
            continue
        else:
            result.append(i)
    for i in hashtag_search:
        if i in result:
            continue
        else:
            result.append(i)

    sentence = list()
    if isKorean(card_name) is True:
        # 한글 토큰화
        okt = Okt()
        for i in related:
            if isKorean(i.title) is True:
                sentence.append(okt.morphs(i.title))
            else:
                sentence.append(word_tokenize(i.title))
    else:
        # 영어 토큰화
        nltk.download('punkt')
        word_tokenize(card_name)
        for i in related:
            if isKorean(i.title) is False:
                sentence.append(word_tokenize(i.title))
            else:
                sentence.append(word_tokenize(i.title))
    # rtn의 개수만큼 for문으로 append하자
    try:
        rtn = find_similar(card_name, sentence, skip_gram=True)
    except:
        context = {'cards': result}
        return render(request, 'quiz/cards.html', context)

    for i in rtn:
        a = Card.objects.filter(title__icontains=i).exclude(title__icontains=card_name).order_by('-likes').values()
        for j in a:
            if j in result:
                continue
            else:
                result.append(j)

    context = {'cards': result}
    return render(request, 'quiz/cards.html', context)


@login_required
def retrive_card(request):
    pk = request.GET.get('pk')
    target_card = Card.objects.filter(pk=pk)[0]
    quizzes_of_target_card = target_card.quiz_set.all()
    if quizzes_of_target_card:
        context = {'quizzes': quizzes_of_target_card}
        return render(request, 'quiz/card_retrieved.html', context)
    else:
        context = {'card': target_card}
        return render(request, 'quiz/card_none.html', context)



# ---------------------------------------
@login_required
def basic_search_view(request):
    today = datetime.date.today()
    form1 = SearchForm()
    data = Search_time.objects.filter(time__contains=today).values('keyword')
    name_list = []
    counts = {}
    for i in data:
        name_list.append(i['keyword'])
    count_repetition(counts, name_list)
    counts = sorted(counts.items(), key=lambda item:item[1], reverse=True)
    ranks = {}
    for i in counts:
        #if i >= len(counts):
           # break
        ranks[i[0]] = i[1]

    context = {
        'form1': form1,
        'ranks': ranks,
        'today': datetime.date.strftime(today, "%Y-%m-%d"),
    }
    return render(request, 'search/search_default.html', context)

@login_required
def search_for_period(request):
    form1 = SearchForm(request.GET)
    form2 = TimeForm()
    from_time = request.GET.get('_from')
    _from = from_time
    to_time = request.GET.get('_to')
    _to = to_time
    from_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
    from_time = datetime.date(from_time.year, from_time.month, from_time.day)
    to_time = datetime.datetime.strptime(to_time, '%Y-%m-%d')
    to_time = datetime.date(to_time.year, to_time.month, to_time.day)
    to_time = to_time + datetime.timedelta(days=1)

    contents = make_data(Search_time, from_time, to_time, 'keyword')

    context = {
        'form1': form1,
        'form2': form2,
        'from': _from,
        'to': _to,
        'contents': contents,
    }

    return render(request, 'search/searched.html', context)

@login_required
def search_for_selected_time(request):
    form1 = SearchForm(request.GET)
    form2 = TimeForm(request.GET)
    from_date = request.GET.get('_from')
    _from = from_date
    from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    from_date = datetime.date(from_date.year, from_date.month, from_date.day)
    to_date = request.GET.get('_to')
    _to = to_date
    to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
    to_date = datetime.date(to_date.year, to_date.month, to_date.day)
    to_date = to_date + datetime.timedelta(days=1)

    time = request.GET.get('select')
    from_time = time.split(' ~ ')[0]
    to_time = time.split(' ~ ')[1]

    contents_for_days = {}
    while from_date < to_date:
        contents = {}
        from_date_start = datetime.datetime(from_date.year, from_date.month, from_date.day, int(from_time), int('00'))
        if to_time == '24':
            if from_date.month in [1,3,5,7,8,10,12] and from_date.day+1 > 31:
                from_date_end = datetime.datetime(from_date.year, from_date.month+1, 1, 00, int('00'))
            elif from_date.month in [2,4,6,9,11] and from_date.day+1 > 30:
                from_date_end = datetime.datetime(from_date.year, from_date.month + 1, 1, 00, int('00'))
            else:
                from_date_end = datetime.datetime(from_date.year, from_date.month, from_date.day + 1, 00, int('00'))
        else:
            from_date_end = datetime.datetime(from_date.year, from_date.month, from_date.day, int(to_time), int('00'))

        data = Search_time.objects.filter(time__gte=from_date_start).exclude(time__gt=from_date_end).values('keyword')
        name_list = []
        count = {}
        for i in data:
            name_list.append(i['keyword'])
        count_repetition(count, name_list)
        counts = sorted(count.items(), key=lambda item: item[1], reverse=True)
        for i in counts:
            contents[i[0]] = i[1]
        contents_for_days[datetime.date.strftime(from_date, "%Y-%m-%d")] = contents
        from_date += datetime.timedelta(days=1)
    context = {
        'form1': form1,
        'form2': form2,
        'from': _from,
        'to': _to,
        'contents' : contents_for_days,
    }

    return render(request, 'search/search_for_time.html', context)


###############################

@login_required
def basic_download_view(request):
    today = datetime.date.today()
    form1 = SearchForm()
    data = Download_time.objects.filter(time__contains=today).values('card_title', 'card')
    contents = {}
    name_list = []
    for i in data:
        content = {}
        name_list.append(i['card_title'])
        content['pk'] = i['card']
        contents[i['card_title']] = content
    count = {}
    count_repetition(count, name_list)
    for i in contents:
        contents[i]['count'] = count[i]
    contents = sorted(contents.items(), key=lambda item: item[1]['count'], reverse=True)
    download_list = {}
    for i in contents:
        download_list[i[0]] = i[1]

    context = {
        'form1': form1,
        'lists': download_list,
        'today': datetime.date.strftime(today, "%Y-%m-%d"),
    }
    return render(request, 'download/download_default.html', context)

@login_required
def download_for_period(request):
    form1 = SearchForm(request.GET)
    form2 = TimeForm()
    from_time = request.GET.get('_from')
    _from = from_time
    from_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
    from_time = datetime.date(from_time.year, from_time.month, from_time.day)
    to_time = request.GET.get('_to')
    _to = to_time
    to_time = datetime.datetime.strptime(to_time, '%Y-%m-%d')
    to_time = datetime.date(to_time.year, to_time.month, to_time.day)
    to_time = to_time + datetime.timedelta(days=1)
    list_for_days = {}
    while from_time < to_time:
        data = Download_time.objects.filter(time__contains=from_time).values('card_title', 'card')
        contents = {}
        name_list = []
        for i in data:
            content = {}
            name_list.append(i['card_title'])
            content['pk'] = i['card']
            contents[i['card_title']] = content
        count = {}
        count_repetition(count, name_list)
        for i in contents:
            contents[i]['count'] = count[i]
        contents = sorted(contents.items(), key=lambda item: item[1]['count'], reverse=True)
        download_list = {}
        for i in contents:
            download_list[i[0]] = i[1]
        list_for_days[datetime.date.strftime(from_time, '%Y-%m-%d')] = download_list
        from_time += datetime.timedelta(days=1)

    context = {
        'form1': form1,
        'form2': form2,
        'from': _from,
        'to': _to,
        'lists': list_for_days,
    }

    return render(request, 'download/download_searched.html', context)

@login_required
def download_for_selected_time(request):
    form1 = SearchForm(request.GET)
    form2 = TimeForm(request.GET)
    from_date = request.GET.get('_from')
    _from = from_date
    from_date = datetime.datetime.strptime(from_date, '%Y-%m-%d')
    from_date = datetime.date(from_date.year, from_date.month, from_date.day)
    to_date = request.GET.get('_to')
    _to = to_date
    to_date = datetime.datetime.strptime(to_date, '%Y-%m-%d')
    to_date = datetime.date(to_date.year, to_date.month, to_date.day)
    to_date = to_date + datetime.timedelta(days=1)

    time = request.GET.get('select')
    from_time = time.split(' ~ ')[0]
    to_time = time.split(' ~ ')[1]

    list_for_days = {}
    while from_date < to_date:
        contents = {}
        from_date_start = datetime.datetime(from_date.year, from_date.month, from_date.day, int(from_time), int('00'))
        if to_time == '24':
            if from_date.month in [1, 3, 5, 7, 8, 10, 12] and from_date.day + 1 > 31:
                from_date_end = datetime.datetime(from_date.year, from_date.month + 1, 1, 00, int('00'))
            elif from_date.month in [2, 4, 6, 9, 11] and from_date.day + 1 > 30:
                from_date_end = datetime.datetime(from_date.year, from_date.month + 1, 1, 00, int('00'))
            else:
                from_date_end = datetime.datetime(from_date.year, from_date.month, from_date.day + 1, 00, int('00'))
        else:
            from_date_end = datetime.datetime(from_date.year, from_date.month, from_date.day, int(to_time), int('00'))
        data = Download_time.objects.filter(time__gte=from_date_start).exclude(time__gt=from_date_end).values('card_title', 'card')
        name_list = []
        count = {}
        for i in data:
            content = {}
            name_list.append(i['card_title'])
            content['pk'] = i['card']
            contents[i['card_title']] = content
        count_repetition(count, name_list)
        for i in contents:
            contents[i]['count'] = count[i]
        contents = sorted(contents.items(), key=lambda item: item[1]['count'], reverse=True)
        download_list = {}
        for i in contents:
            download_list[i[0]] = i[1]
        list_for_days[datetime.date.strftime(from_date, '%Y-%m-%d')] = download_list
        from_date += datetime.timedelta(days=1)
    context = {
        'form1': form1,
        'form2': form2,
        'from': _from,
        'to': _to,
        'lists': list_for_days,
    }
    return render(request, 'download/download_for_time.html', context)


def make_data(category, from_time, to_time, field):
    data = {}
    while from_time < to_time:
        name_list = []
        counts = {}
        count_data = {}
        _object = category.objects.filter(time__contains=from_time).values(field)
        for i in _object:
            name_list.append(i[field])
        count_repetition(counts, name_list)
        counts = sorted(counts.items(), key=lambda item: item[1], reverse=True)
        for i in counts:
            count_data[i[0]] = i[1]
        data[datetime.date.strftime(from_time, '%Y-%m-%d')] = count_data
        from_time += datetime.timedelta(days=1)
    return data

########################################

@login_required
def basic_make_view(request):
    form = MakeSearchForm()
    today = datetime.date.today()
    count_dict = {}
    data = Make_time.objects.filter(time__contains=today).values('time')
    for i in data:
        key = datetime.datetime.strftime(i['time'], "%H") + ':00 ~ ' + \
              datetime.datetime.strftime(i['time'] + datetime.timedelta(hours=1), "%H") + ':00'
        try:
            count_dict[key] += 1
        except:
            count_dict[key] = 1
    for i in range(0, 24):
        key = str(i) + ':00 ~ ' + str(i + 1) + ':00'
        if (i + 1) == 24:
            key = str(i) + ':00 ~ ' + '00:00'
        try:
            count_dict[key] += 0
        except:
            count_dict[key] = 0
    count_tuple = sorted(count_dict.items(), key=lambda item: item[1], reverse=True)
    count_for_hours = {}
    for i in count_tuple:
        count_for_hours[i[0]] = i[1]
    context = {
        'form': form,
        'lists': count_for_hours,
        'today': today,
    }
    return render(request, 'make/make_default.html', context)

@login_required
def make_for_period(request):
    form = MakeSearchForm(request.GET)
    from_time = request.GET.get('_from')
    from_time = datetime.datetime.strptime(from_time, '%Y-%m-%d')
    from_time = datetime.date(from_time.year, from_time.month, from_time.day)
    to_time = request.GET.get('_to')
    to_time = datetime.datetime.strptime(to_time, '%Y-%m-%d')
    to_time = datetime.date(to_time.year, to_time.month, to_time.day)
    to_time = to_time + datetime.timedelta(days=1)

    count_for_days = {}
    while from_time < to_time:
        count_dict = {}
        data = Make_time.objects.filter(time__contains=from_time).values('time')
        for i in data:
            key = datetime.datetime.strftime(i['time'], "%H") + ':00 ~ ' + \
                  datetime.datetime.strftime(i['time'] + datetime.timedelta(hours=1), "%H") + ':00'
            try:
                count_dict[key] += 1
            except:
                count_dict[key] = 1
        for i in range(0, 24):
            key = str(i) + ':00 ~ ' + str(i+1) + ':00'
            if (i+1) == 24:
                key = str(i) + ':00 ~ ' + '00:00'
            try:
                count_dict[key] += 0
            except:
                count_dict[key] = 0
        count_tuple = sorted(count_dict.items(), key=lambda item: item[1], reverse=True)
        count_for_hours = {}
        for i in count_tuple:
            count_for_hours[i[0]] = i[1]
        key_for_days = datetime.date.strftime(from_time, "%Y-%m-%d")
        count_for_days[key_for_days] = count_for_hours
        from_time += datetime.timedelta(days=1)

    context = {
        'form': form,
        'counts': count_for_days,
    }

    return render(request, 'make/make_searched.html', context)


def count_repetition(count, name_list):
    lists = []
    for i in name_list:
        try: count[i] += 1
        except: count[i] = 1




@csrf_exempt
@login_required
def add_card_from_csv(request):
    if request.method=="POST":
        file = request.FILES['csv_file']

        if not file.name.endswith(".csv"):
            messages.error(request,"파일이 csv 형식이 아닙니다.")
            return redirect('main')

        decoded_file = file.read().decode('cp949').splitlines()
        rdr = csv.reader(decoded_file)
        info=[]

        for row in rdr:
            a,b,c=row
            tuple=(a,b,c)
            info.append(tuple)
        file.close

        le=len(info)

        for i in range(le):
            if i==0:
                new_cards = Card.objects.create(user_name=info[i][0],title=info[i][1],description=info[i][2])
            else:
                new_Quiz = Quiz.objects.create(card=new_cards, question=info[i][0], answer=info[i][1])

        return redirect('main')