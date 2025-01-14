from google.colab import drive
import requests
from bs4 import BeautifulSoup
from collections import defaultdict, Counter
import time
import random
import os
import operator


def others_watched(l: list, not_in: list, more_than: int = 0):
    movies = []
    for elem in l:
        temp = _read_list(elem)
        movies.extend(temp)
    d = dict(Counter(movies))
    d = sorted_dict = dict(sorted(d.items(), key=operator.itemgetter(1), reverse=True))
    if more_than != 0:
        d = dict((k, v) for k, v in d.items() if v > more_than)

    seen = _read_list(not_in)
    d = {k: v for k, v in d.items() if k not in seen}

    return d


def create_ignore_file(empty_lists, folder):
    path = f"gdrive/MyDrive/{folder}/{empty_lists}.txt"

    if not os.path.exists(path):
        with open(path, "w") as f:
            pass


def remove_ignore_file(empty_lists, folder):
    path = f"gdrive/MyDrive/{folder}/{empty_lists}.txt"

    if os.path.exists(path):
        os.remove(path)


def conn_to_drive(remount: bool = False) -> None:
    """
    Connects user to Google drive. After running the function the user needs to
    choose the email that is connected with the Google drive they want to use,
    then click "xontinue" two times.

    Input:
        remount (optional, default - False) - bool, to forcefully reconnect to
        Google Drive.
    Output:
        None.
    """

    drive.mount("/content/gdrive/", force_remount=remount)


def movie_strip(movie: str) -> str:
    """
    Deletes spaces from both sides of a movie title string.

    Input:
        movie - str, movie title.
    Output:
      movie - str, movie title without spaces.
    """

    while movie[0] == " ":
        movie = movie.lstrip()
    while movie[-1] == " ":
        movie = movie.strip()

    return movie


def get_all_users(l: list) -> list:
    """
    Gets users from the list of all movie list files.

    Input:
        l - list, a list of movie list files.
    Output:
        list of Letterboxd users whose watched, watchlisted movie lists are in the inputted list.
    """

    return list(set([w.split(" ")[-1].split(".")[0] for w in l]))


def get_user_files(folder: str, exclude: list = []) -> list:
    """
    Input:
        folder - str, a folder with files in Google Drive.
        exclude - list (optional, default - empty list), files to exclude.
    Output:
        list of files that are either watched or watchisted movie lists.
    """

    watched = []
    ed = "Watched"
    li = "Watchlist"

    with open(f"gdrive/MyDrive/{folder}/requests.txt", "w+") as f:
        files = os.listdir(f"gdrive/MyDrive/{folder}")

        for fil in files:
            if (
                fil.endswith(".txt")
                and "|" in fil
                and ((fil[: len(ed)] == ed) or (fil[: len(li)] == li))
                and fil not in exclude
            ):
                _, author = fil.split(" | ")
                author = author.split(".")[0]
                watched.append(fil)

    return watched


def _get_num_of_pages(user: str, which: str) -> int:
    """
    Input:
        user - str, a username of a Letterboxd user
        which - str, a type of movie list to get the last page of
    Output:
        an number of the last page of the list
    """

    which = which.lower()

    if which == "watched":
        url = f"https://letterboxd.com/{user}/films"
    else:
        url = f"https://letterboxd.com/{user}/watchlist"

    soup = _get_html(url)
    last_page = _get_last_page(soup)
    return last_page


def _get_last_movie(link: str) -> str:
    """ """

    html = _get_html(link)
    soup = html.find_all("div", class_="poster")
    last_movie = soup[-1]
    movie_link = f'https://letterboxd.com{last_movie["data-film-slug"]}'
    return _get_title_and_year(movie_link)


def _get_last_movies(link, pages: int) -> list:
    return [_get_last_movie(f"{link}/page/{i}/") for i in range(1, pages + 1)]


def _get_last_movie_index(movie: str, file: str, folder) -> str:
    with open(f"gdrive/MyDrive/{folder}/{file}", "r") as f:
        films = f.read().split("\n")
    try:
        return films.index(movie)
    except:
        return None


def get_full_pages(link: str, file_: str, folder):
    html = _get_html(link)
    last_page = _get_last_page(html)
    last_movies = _get_last_movies(link, last_page)
    last_index = []
    for lm in last_movies:
        ind = _get_last_movie_index(lm, file_, folder)
        if ind != None:
            last_index.append(ind)
        else:
            last_index.append(None)
            break
    return last_index.index(None), last_index


def _get_watched_num(user: str, this_year=False):
    url = f"http://www.letterboxd.com/{user}"

    soup = _get_html(url)

    soup = soup.find_all("span", class_="value")
    inter = str(soup[0]).split("</")[0].split(">")[-1]

    if this_year:
        inter = str(soup[1]).split("</")[0].split(">")[-1]

    if "," in inter:
        inter = inter.replace(",", "")

    return int(inter)


def get_percentage_watched(user_list, your_username, l: list, folder):
    if your_username in user_list:
        user_list.remove(your_username)

    for us in user_list:
        watched_movies = compare_lists([f"Watched | {us}.txt", f"{l}.txt"], folder)
        watchlisted = compare_lists([f"Watchlist | {us}.txt", f"{l}.txt"], folder)
        nw_watched = compare_lists(
            [f"Watched | {us}.txt", f"{l}.txt"],
            folder,
            watched=True,
            watched_list=f"Watched | {your_username}",
        )
        nw_watchlisted = compare_lists(
            [f"Watchlist | {us}.txt", f"{l}.txt"],
            folder,
            watched=True,
            watched_list=f"Watched | {your_username}",
        )

        all_movies = len(watched_movies) + len(watchlisted)
        not_watched = len(nw_watched) + len(nw_watchlisted)

        try:
            if int(round(not_watched / all_movies * 100, 0)) != 0:
                print(f"{us}, {100 - int(round(not_watched/all_movies*100,0))}%")

        except:
            pass


def get_watched_comparison(
    your_username: str, users: list = [], all: bool = False, this_year=False
):
    if your_username in users:
        users.remove(your_username)
    you = _get_watched_num(your_username, this_year=this_year)

    user_dict = {}

    for u in users:
        n = _get_watched_num(u, this_year=this_year)
        if not all:
            if n > you:
                user_dict[u] = n
        else:
            user_dict[u] = n
    user_dict = dict(sorted(user_dict.items(), key=lambda x: x[1], reverse=True))
    for k, v in user_dict.items():
        print(f"{k}: {v} | {int(round(100*v/you-100))}% | {v-you}")
    if not all:
        print(f"{your_username}: {you}")


def rewrite_list_up_to(file: str, index: int, folder):
    with open(f"gdrive/MyDrive/{folder}/{file}", "r") as f:
        films = f.read().split("\n")
    films = films[:index]
    with open(f"gdrive/MyDrive/{folder}/{file}", "w") as f:
        for m in films:
            f.write(m + "\n")


def get_sorted_page_dict(l: list, which) -> list:
    page_nums = []
    for us in l:
        page_nums.append(_get_num_of_pages(us, which))

    user_pages = {up: page_num for up, page_num in zip(l, page_nums)}
    return list(
        {k: v for k, v in sorted(user_pages.items(), key=lambda item: item[1])}.keys()
    )


def get_all_files(folder: str, exclude: list = []):
    lb_lists = []

    if not os.path.exists(f"gdrive/MyDrive/{folder}/requests.txt"):
        with open(f"gdrive/MyDrive/{folder}/requests.txt", "w") as f:
            pass

    with open(f"gdrive/MyDrive/{folder}/requests.txt", "w+") as f:
        files = os.listdir(f"gdrive/MyDrive/{folder}")

        for fil in files:
            if (
                fil.endswith(".txt")
                and fil not in exclude
                and ("|" in fil)
                and fil not in exclude
            ):
                _, author = fil.split(" | ")
                author = author.split(".")[0]
                lb_lists.append(fil)

    return lb_lists


def add_watched(movie: str, year: str, folder: str, user: str) -> None:
    movie = movie_strip(movie)

    movie_year = f"{movie}, {year}"
    title = f"Watched | {user}"

    with open(f"gdrive/MyDrive/{folder}/{title}.txt", "a") as f:
        f.write(f"{movie_year}\n")

    watchlist = f"gdrive/MyDrive/{folder}/Watched | {user}.txt"

    if os.path.exists(watchlist):
        watchedl_movies = _read_list(watchlist, folder)
        if movie_year in watchedl_movies:
            watchedl_movies.remove(movie_year)

        with open(f"gdrive/MyDrive/{folder}/Watched | {user}.txt", "w") as f:
            for wlm in watchedl_movies:
                f.write(f"{wlm}\n")


def get_to_watch(
    watched: list,
    folder: str,
    empty_file: str,
    exclude: dict = {"False": None},
    add_lists: list = [],
    more_than: int = 0,
):
    movies_count = defaultdict(int)
    exclude_key = next(iter(exclude.keys()), None)
    watched_list = exclude.get(exclude_key, []) + ".txt"

    create_ignore_file(empty_file, folder)
    exclude = _read_from_file(empty_file, folder)
    new_exclude = []

    for w in watched:
        if w not in exclude:
            l = [w] + [f"{al}.txt" for al in add_lists]
            iner = compare_lists(
                l, folder, watched=bool(exclude), watched_list=watched_list
            )
            if len(iner) > 0:
                for i in iner:
                    movies_count[i] += 1
            else:
                new_exclude.append(w)

    with open(f"gdrive/MyDrive/{folder}/{empty_file}.txt", "w+") as f:
        for ne in new_exclude:
            f.write(f"{ne}\n")

    movies_dict = dict(
        sorted(movies_count.items(), key=lambda item: item[1], reverse=True)
    )
    return {
        key: val - 1
        for key, val in movies_dict.items()
        if val > more_than and val - 1 > 0
    }


def get_movies_that_user_saw(user, folder, comp_list, exclude=False, exclude_list=None):
    movies = []

    file_name = f"gdrive/MyDrive/{folder}/Watched | {user}.txt"
    goal_file_name = f"gdrive/MyDrive/{folder}/{comp_list}.txt"

    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            l = f.readlines()
            l = [el[:-1] for el in l]
        movies.extend(l)

    if os.path.exists(goal_file_name):
        with open(goal_file_name, "r") as f:
            mine = f.readlines()
            mine = [m[:-1] for m in mine]

    inters = set(movies) & set(mine)

    if exclude and exclude_list:
        excl = _read_list(exclude_list)

        return inters - set(excl)
    else:
        return inters


def get_who_saw(movie: str, users: list, folder) -> list:
    saw = []
    for u in users:
        if os.path.exists(f"gdrive/MyDrive/{folder}/Watchlist | {u}.txt"):
            with open(f"gdrive/MyDrive/{folder}/Watchlist | {u}.txt", "r") as f:
                l = f.readlines()
                l = [el[:-1] for el in l]
                if movie in l:
                    saw.append(u)
        if os.path.exists(f"gdrive/MyDrive/{folder}/Watched | {u}.txt"):
            with open(f"gdrive/MyDrive/{folder}/Watched | {u}.txt", "r") as f:
                l = f.readlines()
                l = [el[:-1] for el in l]
                if movie in l:
                    saw.append(u)

    return saw


def add_watchlisted(movie: str, year: str, folder: str, user: str):
    movie = movie_strip(movie)

    movie_year = f"{movie}, {year}"
    title = f"Watchlist | {user}"

    with open(f"gdrive/MyDrive/{folder}/{title}.txt", "a") as f:
        f.write(movie_year + "\n")


def _read_list(file_name, folder):
    movie_list = _read_from_file(file_name, folder)
    if len(movie_list[-1]) == 0:
        movie_list = movie_list[:-1]
    return movie_list


def _read_from_file(file_name: str, folder: str):
    if "/" in file_name:
        file_name = file_name.split("/")[-1]
    if ".txt" not in file_name:
        file_name += ".txt"
    link = f"gdrive/MyDrive/{folder}/{file_name}"
    print(link)
    with open(link, "r") as f:
        movies = f.read().split("\n")
    return movies


def compare_lists(
    lists: list,
    folder: str,
    union: bool = True,
    watched: bool = False,
    watched_list=None,
    random_movie: bool = False,
    random_movie_size: int = 1,
    length: bool = False,
) -> list:
    movies = []
    for lst in lists:
        file_name = lst
        file_path = os.path.join(f"gdrive/MyDrive/{folder}", file_name)

        if ".txt" not in file_path:
            file_path += ".txt"
        if not os.path.exists(file_path):
            print(f"There is no {file_name}.")
            continue

        movies.extend(list(set(_read_list(file_name, folder))))

    movies = list(set([x for x in movies if movies.count(x) > (len(lists) - 1)]))

    if watched and watched_list:
        watched_set = set(_read_list(watched_list, folder))
        movies = [m for m in movies if m not in watched_set]

    if random_movie:
        return random.sample(movies, random_movie_size)
    elif length:
        return len(movies)
    else:
        return movies


def get_watchlist(
    author: str, folder, title: str = "Watchlist", print_links: bool = False
):
    watchlist_url = f"https://letterboxd.com/{author}/watchlist"
    title = f"{title} | {author}"

    movies = _get_movies_v2(watchlist_url, print_links)

    with open(f"gdrive/MyDrive/{folder}/{title}.txt", "w+") as f:
        for m in movies:
            f.write(f"{m}\n")


def get_watched(author: str, folder, title: str = "Watched", print_links: bool = False):
    watched_url = f"https://letterboxd.com/{author}/films"
    title = f"{title} | {author}"

    movies = _get_movies_v2(watched_url, print_links)

    with open(f"gdrive/MyDrive/{folder}/{title}.txt", "w") as f:
        for m in movies:
            f.write(f"{m}\n")


def _get_html(url):
    soup = requests.get(url)
    return BeautifulSoup(soup.content, "html.parser")


def _get_last_page(soup):
    check = soup.find("li", class_="paginate-page")
    if check:
        return int(soup.find_all("li", class_="paginate-page")[-1].getText())
    return 1


def _get_title_and_year(link: str):
    movie_page = _get_html(link)
    title_year = str(movie_page.find("meta", property="og:title")["content"])
    if "(" in title_year:
        title = title_year.split("(")[0][:-1]
        year = title_year.split("(")[1][:-1]
    else:
        title = title_year
        year = ""
    return f"{title}, {year}"


def get_new_list(author, folder, print_links: bool = False, range_: tuple = None):
    url = author
    soup = _get_html(url)
    author = url.split("/")[3]
    lst = soup.find_all("h1", class_="title-1")

    lst = str(lst[0])
    lst = lst.split("</")[0].split(">")[1]
    lst = lst.replace("/", " ")
    file_name = lst + " | " + author

    last = _get_last_page(soup)

    print(f"{url} {str(last)}")

    if range_:
        first, _ = range_
        if first == 1:
            mode = "w+"
        else:
            mode = "a"
    else:
        mode = "w+"

    movie_list = _get_movies_v2(url, print_links=print_links, range_=range_)

    with open(f"gdrive/MyDrive/{folder}/{file_name}.txt", mode) as f:
        for movie in movie_list:
            f.write(f"{movie}\n")


def _get_movies_v2(url: str, print_links=False, range_: tuple = None):
    soup = _get_html(url)
    movies = []
    end = False
    last_page = _get_last_page(soup)

    if range_:
        first, last = range_
        last += 1
        if last > last_page:
            last = last_page
    else:
        first, last = 1, last_page + 1

    for p in range(first, last):
        print(f"page {str(p)}/{str(last_page)}")
        page_url = f"{url}/page/{str(p)}"
        soup = _get_html(page_url)
        soup = soup.find_all("div", class_="poster")
        soup = str(soup).split(" ")
        soup = [s for s in soup if "data-target-link=" in s]

        for movie in soup:
            time.sleep(1)
            link = movie[24:-1]
            movie_link = f"https://letterboxd.com/film/{link}"
            if print_links:
                print(f"   {str(movie_link)}")
            title_year = _get_title_and_year(movie_link)
            movies.append(f"{title_year}")
    return movies
