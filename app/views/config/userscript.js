// ==UserScript==
// @name        CouchPotato UserScript
// @description Add movies to your CouchPotato via external sites like IMDB
// @include     http*://*.imdb.com/title/tt*
// @include     http*://imdb.com/title/tt*
// @include     ${host}*
// @include     http://*.sharethe.tv/movies/*
// @include     http://sharethe.tv/movies/*
// @include     http://*.moviemeter.nl/film/*
// @include     http://moviemeter.nl/film/*
// @include     http://whiwa.net/stats/movie/*
// @include     http://trailers.apple.com/trailers/*
// @include     http://www.themoviedb.org/movie/*
// @include     http://www.allocine.fr/film/* 
// @include     http://trakt.tv/movie/*
// @include     http://*.trak.tv/movie/*
// @include     http://www.rottentomatoes.com/m/*
// @include     http://www.youtheater.com/view.php?*
// @include     http://youtheater.com/view.php?*
// @include     http://www.sratim.co.il/view.php?*
// @include     http://sratim.co.il/view.php?*
// @exclude     http://trak.tv/movie/*/*
// @exclude     http://*.trak.tv/movie/*/*
// @include     http://*.filmweb.pl/*
// @include     http://filmweb.pl/*
// ==/UserScript==

var version = 9;

function create() {
    switch (arguments.length) {
    case 1:
        var A = document.createTextNode(arguments[0]);
        break;
    default:
        var A = document.createElement(arguments[0]), B = arguments[1];
        for ( var b in B) {
            if (b.indexOf("on") == 0){
                A.addEventListener(b.substring(2), B[b], false);
            }
            else if (",style,accesskey,id,name,src,href,which".indexOf(","
                    + b.toLowerCase()) != -1){
                A.setAttribute(b, B[b]);
            }
            else{
                A[b] = B[b];
            }
        }
        for ( var i = 2, len = arguments.length; i < len; ++i){
            A.appendChild(arguments[i]);
        }
    }
    return A;
}

if (typeof GM_addStyle == 'undefined'){
    GM_addStyle = function(css) {
        var head = document.getElementsByTagName('head')[0], style = document
                .createElement('style');
        if (!head) {
            return
        }
        style.type = 'text/css';
        style.textContent = css;
        head.appendChild(style);
    }
}

// Styles
GM_addStyle('\
    #mmPopup { opacity: 0.5; width:200px; font-family: "Helvetica Neue", Helvetica, Arial, Geneva, sans-serif; -moz-border-radius-topleft: 6px; -moz-border-radius-topright: 6px; -webkit-border-top-left-radius: 6px; -webkit-border-top-right-radius: 6px; -moz-box-shadow: 0 0 20px rgba(0,0,0,0.5); -webkit-box-shadow: 0 0 20px rgba(0,0,0,0.5); position:fixed; z-index:9999; bottom:0; right:0; font-size:15px; margin: 0 20px; display: block; background:#f5f5f5; } \
    #mmPopup:hover { opacity: 1; } \
    #mmPopup a#addTo { cursor:pointer; text-align:center; text-decoration:none; color: #000; display:block; padding:15px 0 10px; } \
    #mmPopup a#closeBtn { cursor:pointer; float: right; padding:10px; } \
    #mmPopup a img { vertical-align: middle; } \
    #mmPopup a:hover { color:#000; } \
    #mmPopup iframe{ background:#f5f5f5; margin:6px; height:70px; width:188px; overflow:hidden; border:none; } \
');

var cpLocation = '${host}';
var movieImg = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAZCAYAAABQDyyRAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAA+9JREFUeNrMVklIXFkUPVWWY5cDccIpMQ444YCi7UJ3KrpUxAkURRAFW6GdMCI0ooKuxIWCIkrc6FYMcYogrgxoEHFeRFRE42w5D/X73dv1i4pUOiGmkly4/u9779c979x7z3sKSZLwK02JX2y/BYCXwmeESybyGV0Mo6YQNTBzf38f09/fj7GxMRwcHPyQnTk5OSEpKQm5ublQqVTvxdCfXwIg9fT0YGBgAO7u7qipqUFAQACurq7Q29uLoaEhXhgdHY3q6mqo1WocHx+jpaUF8/PzPJeamor8/HwKhKWlJbS2tmJ/f5/nsrKyUFhYSK8vhG8+BmD2j7Dm5mZotVqcnp5ibW0N4eHhcHFxQUREBM7OznhsZ2cHu7u7iI2Nhb29PQOi8b29PaysrECpVCIqKgpubm4IDAzE7OwsLi8vsbW1hYyMDIrVK/yTUQDd3d2oqKjgjygFc3NzCAsLg7OzMyIjI3F+fo7V1VVsbm5ie3sbMTExsLW15acMYmFhAbe3twza1dUVwcHB0Gg0WF9fR15eHsXqNAZA3wUJCQkoKipiGilIQ0MDf2xmZsYUJicn87rp6Wmm+OLigpmglIWEhPDc4OAg+vr6cH19zSwUFBR8tVa4BhITE03aauPj4/QIE75gFMBPanmjAFT05ycxYNRU8svo6CiGh4fR2dkJoQvw8PBAXV0dfHx8cHNzw+MjIyO8Ni4uDpWVlbCxseGibWpqwuLiIs9lZ2cjJycHlpaW3DlTU1N6afhfABMTE+jq6uLgnp6eqK+v5+BU2aQTcvD4+HhUVVXB2toaJycnrAdy8MzMTNYDasnl5WUeIzA6eyWc0GiNdkFbWxvvlIKKzvxs57IYGQYnMWpsbNSLEQWibqHgBIiA2dnZIS0tDbW1taxlwm0o3YYp1zNwd3fHSlheXs4MUO+TElJaZCUsKyuDubk5q9xjJaTd02/ISkgAqR1JCw4PD+XNSiZvQysrKygUClhYWDCrpAX+/v7o6OjQiOkA4RpdGi4/Y+Cp5uDggJKSEj5HiAkCQSmU2T06OlILuadikURqbgXAt+K9khlIT0/nc+ApRqceSe63/FZQUBDa29vp9W9mICUlhU/DJ10slP/Vs6+vLx9gZNRRGxsb3JJeXl76td7e3vrPiIEPYmEEtdrk5CRR9V0AHB0dUVpaitDQUD0gOmGJEV0NUAEeGVxU3gn/CwLAS7qUSCYwUf2SOOSk4uJi+vdYuJtwtfA/6AQgpxR81N1WnIU//4EKbP7w8PBGPJ9REersTHTchaE8G3bBvs6fZHJLiwBW4vakJfr9/Py4JIx+IFNhAqf6em2QkT7hysfr/hVgAIhbr+v/xmSzAAAAAElFTkSuQmCC'
var closeImg = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAAsTAAALEwEAmpwYAAAABGdBTUEAALGOfPtRkwAAACBjSFJNAAB6JQAAgIMAAPn/AACA6QAAdTAAAOpgAAA6mAAAF2+SX8VGAAAA5ElEQVR42tRTQYoEIQwsl/2Bl3gQoY9eBKEf5kvyG8G7h4Z+S38gIu5lp5lZ2R7YPm1BDhZJSFWiGmPgDj5wE7cbfD4/mBkAHprUj9yTTyn9OsGIMSLG+Fxwxc8SiAi9d4QQHskjhIDeO4jorQcq5wwiQmsN3nt479FaAxEh5zxJmyZIKalSClprL1FKQUpJXZr4DBH52xqZeRhjICKw1sJaCxGBMQbMPN41GFpriAicc6i1otYK5xxEBFrraQuThGVZAADbtp2amXms6woAOI7j0gO17/t5MN+HNfEvBf//M30NAKe7aRqUOIlfAAAAAElFTkSuQmCC'

lib = (function(){
    var _public = {}
    var osd = function(id, year){
        var navbar, newElement;
        //var year = document.getElementsByTagName('h1')[0].getElementsByTagName('a')[0].text

        var iFrame = create('iframe', {
          src : cpLocation + "movie/imdbAdd/?id=" + id + '&year=' + year,
          frameborder : 0,
          scrolling : 'no'
        })

        var addToText = '<a class="addTo" href="#"></a>'
        var popupId = 'mmPopup'

        var popup = create('div', {
          id : popupId,
          innerHTML : addToText
        });
        var addButton = create('a', {
            innerHTML: '<img src="' + movieImg + '" />Add to CouchPotato',
            id: 'addTo',
            onclick: function(){
                popup.innerHTML = '';
                popup.appendChild(create('a', {
                    innerHTML: '<img src="' + closeImg + '" />',
                    id: 'closeBtn',
                    onclick: function(){
                        popup.innerHTML = '';
                        popup.appendChild(addButton);
                    }
                }));
            popup.appendChild(iFrame);
          }
        }) //create
        popup.appendChild(addButton);

        document.body.parentNode.insertBefore(popup, document.body);
    } //end osd

    _public.osd = osd
    return _public
})();

/*
 * TMDB's Api object to be used in all of the sites needed it.
 */
tmdb_api = (function(){
    var _public = {};
    var TMDB_API_KEY = "31582644f51aa19f8fcd9b2998e17a9d";
    var TMDB_BASE_URL = "http://api.themoviedb.org/2.1/";
    var saved_year = null;
    
    /*
     *  AJAX post and call 'callback' function
     */
    function post(newurl, callback) {
        GM_xmlhttpRequest({
            method: 'GET',
            url: newurl,
            headers: {
            'User-agent': 'Mozilla/4.0 (compatible) Greasemonkey',
                'Accept': 'application/atom+xml,application/xml,text/xml'
            },
            onload: function(responseDetails) {
                callback(responseDetails);
            }
        });
    }
    
    var _BuildTmdbUrl = function(Func, Arg) {
        return TMDB_BASE_URL + Func + '/en/xml/' + TMDB_API_KEY + '/' + Arg;
    }
        
    var _PostFromTmdbXml = function(response) {
        var Movies = null;
        var i = 0;
        var curMovie = null;
        var year = null;
        var imdb_id = null;
        
        if ( !response ) {
            return;
        }
        
        if ((window.navigator.userAgent.indexOf("Chrome") > 0) || (!response.responseXML)) {
            response.responseXML = new DOMParser().parseFromString(response.responseText, "text/xml");
        }
        
        // Makes sure i choose the right choice.
        Movies = response.responseXML.getElementsByTagName('movie');
        for ( i = 0 ; i < Movies.length ; i ++ ) {
            curMovie = Movies[i];
            imdb_id = curMovie.getElementsByTagName('imdb_id')[0].firstChild.nodeValue; 
            year = curMovie.getElementsByTagName('released')[0].firstChild.nodeValue.substr(0, 4);
            
            // if year selected, i'll choose the right year only.
            if ( saved_year == year ) {
                lib.osd(imdb_id, year);
                return;
            }
        }
        
        // if there is no saved year, i'll choose the last choice.
        if ( !saved_year ) {
            lib.osd(imdb_id, year);
        }
    }
        
    var _MovieSearch = function(Name, Year) {
        var escapedName = Name.replace(/ /g, "+").replace(/\//g,"-");
        escapedName = escapedName.replace(/\(.+?\)/g, ""); // Strip ()
        var url = _BuildTmdbUrl('Movie.search', escapedName);
        
        // Saves the year to query later on.
        if ( Year ) {
            saved_year = Year;
        }
        
        post(url, _PostFromTmdbXml);
    }
        
    var _MovieSearchById   = function(TmdbId) {
        var url = _BuildTmdbUrl('Movie.getInfo', TmdbId);
        post(url, _PostFromTmdbXml);
    }
    
    _public.MovieSearch = _MovieSearch;
    _public.MovieSearchById = _MovieSearchById;
    return _public;
})();
    
imdb = (function(){
    function isMovie(){
        var series = document.getElementsByTagName('h5')
        for (var i = 0; i < series.length; i++) {
            if (series[i].innerHTML == 'Seasons:') {
                return false;
            }
        }
        return true;
    }

    function getId(){
        var regex = new RegExp(/tt(\d+)/);
        var id = location.href.match(regex)[0];
        return id;
    }

    function getYear(){
        try {
            return document.getElementsByTagName('h1')[0].getElementsByTagName('a')[0].text;
        } catch (e) {
            var spans = document.getElementsByTagName('h1')[0].getElementsByTagName('span');
            var pattern = /^\((TV|Video) ([0-9]+)\)$/;
            for (var i = 0; i < spans.length; i++) {
                if (spans[i].innerHTML.search(pattern)) {
                    return spans[i].innerHTML.match(pattern)[1];
                }
            }
        }
    }

    var constructor = function(){
        if(isMovie()){
            lib.osd(getId(), getYear());    
        }
    }

    return constructor;
})();

sharethetv = (function(){

    function isMovie(){
        var pattern = /movies\/[^/]+\/?$/;
        matched = location.href.match(pattern);
        return null != matched;
    }

    function getId(){
        var pattern = /imdb\.com\/title\/tt(\d+)/;
        var html = document.getElementsByTagName('html')[0].innerHTML;
        var imdb_id = html.match(pattern)[1];
        return 'tt'+imdb_id;

    }

    function getYear(){
        var pattern = /(\d+)[^\d]*$/;
        var html = document.getElementsByTagName('html')[0].innerHTML;
        var year = html.match(pattern)[1];
        return year;

    }

    function constructor(){
        if(isMovie()){
            lib.osd(getId(), getYear());    
        }
    }
    return constructor;
})();

moviemeter = (function(){

    function isMovie(){
        var pattern = /[^/]+\/?$/;
        var html = document.getElementsByTagName('h1')[0].innerHTML
    matched = location.href.match(pattern);
        return null != matched;
    }

    function getId(){
        var pattern = /imdb\.com\/title\/tt(\d+)/;
        var html = document.getElementsByTagName('html')[0].innerHTML;
        var imdb_id = html.match(pattern)[1];
        return 'tt'+imdb_id;

    }

    function getYear(){
        var pattern = /(\d+)[^\d]*$/;
        var html = document.getElementsByTagName('h1')[0].innerHTML;
        var year = html.match(pattern)[1];
        return year;

    }

    function constructor(){
        if(isMovie()){
            lib.osd(getId(), getYear());    
        }
    }
    return constructor;
})();

whiwa = (function(){

    function isMovie(){
        var pattern = /[^/]+\/?$/;
        var html = document.getElementsByTagName('h3')[0].innerHTML
        matched = location.href.match(pattern);
        return null != matched;
    }

    function getId(){
        var pattern = /imdb\.com\/title\/tt(\d+)/;
        var html = document.getElementsByTagName('html')[0].innerHTML;
        var imdb_id = html.match(pattern)[1];
        return 'tt'+imdb_id;

    }

    function getYear(){
        var pattern = /(\d+)[^\d]*$/;
        var html = document.getElementsByTagName('h3')[0].innerHTML;
        var year = html.match(pattern)[1];
        return year;

    }

    function constructor(){
        if(isMovie()){
            lib.osd(getId(), getYear());    
        }
    }
    return constructor;
})();

trakt = (function(){
    var imdb_input = null;
    var year_input = null;

    function isMovie(){
        imdb_input = document.getElementById("meta-imdb-id");
        year_input = document.getElementById("meta-year");
        return (null != imdb_input) && (null != year_input);
    }

    function getId(){
        return imdb_input.value;
    }

    function getYear(){
        return year_input.value;
    }

    function constructor(){
        if(isMovie()){
            lib.osd(getId(), getYear());    
        }
    }
    return constructor;
})();

apple = (function(){
    /*
     *  Only movies on Apple Trailers
     */
    function isMovie(){
        return true;
    }

    /*
     *  returns movie's name from page's title.
     *
     */
    function getName() {
        return document.title.substr(0, document.title.indexOf(" -"));
    }

    /*
     *  returns year from movie copyright notice.
     *
     */ 
    function getYear() {
        var fullReleaseDate = document.getElementById("view-showtimes").parentNode.innerHTML;
        var justYear = fullReleaseDate.substr(fullReleaseDate.indexOf("Copyright", 0)+12, 4);

        return justYear;
    }

    function constructor(){
        if(isMovie()){
            // Do a search using tmdb_api.
            tmdb_api.MovieSearch(getName(), getYear());
        }
    }
    return constructor;
})();

tmdb = (function(){
    var obj = this;

    function isMovie(){
        return true;
    }

    /*
     *      Returns TMDB id from the url.
     */
    function getTmdbId() {
        var tmdb_id = location.href.match(/movie\/(\d+)/g)[0].substr(6);
        return tmdb_id;
    }

    function constructor(){
        if(isMovie()){
            tmdb_api.MovieSearchById(getTmdbId());
        }
    }
    return constructor;
})();

allocine = (function(){
    function isMovie(){
        var pattern = /fichefilm_gen_cfilm=\d+?\.html$/;
        matched = location.href.match(pattern);
        return null != matched;
    }

    function getName() {
            var mName = document.title.substr(0, document.title.indexOf(" -"));
            return mName;
    }
    
    function getYear(){
        var year = "";
        if(document.title)
        {
            var mName = document.title.substr(0, document.title.indexOf(" -")).replace(/ /g, "+");
            year = mName.substr(document.title.indexOf("(")+1).replace(")","");
        }
        return year;
    }

    function constructor(){
        if(isMovie()){
            tmdb_api.MovieSearch(getName(), getYear());
        }
    }

    return constructor;
})();

rotten = (function(){
    var obj = this;

    function isMovie(){
        return true;
    }

    /*
     *      Search TheMovieDB for IMDB ID, year of release and open OSD
     *
     */
    function getName() {
        var mName = document.title.substr(0, document.title.indexOf("Rotten")-3);
        return mName;
    }

    function getYear() {
        var rightCol = document.getElementById("movieSynopsis").parentNode.getElementsByTagName("div")[1];
        var releaseDate = rightCol.getElementsByTagName("span")[0].getElementsByTagName("span")[0].attributes["content"];

        return releaseDate.value.substr(0, 4);
    }

    function constructor(){
        if(isMovie()){
            tmdb_api.MovieSearch(getName(), getYear());
        }
    }
    return constructor;
})();

youtheater = (function(){
    var obj = this;

    function isMovie(){
        return true;
    }

    /*
     *      Search TheMovieDB for IMDB ID, year of release and open OSD
     *
     */
    function getId() {
        var pattern = /imdb\.com\/title\/tt(\d+)/;
        var html = document.getElementsByTagName('html')[0].innerHTML;
        var imdb_id = html.match(pattern)[1];
        return 'tt'+imdb_id;
    }

    function getYear(){
        var spans = document.getElementsByTagName('span');
        var obj = null;
        for (i = 0; i < spans.length; i ++) {
            obj = spans[i];
            if ( obj.className == 'yearpronobold' ) {
                return obj.innerText.match(/\((19|20)[\d]{2,2}\)/)[0].substr(1, 4);
            }
        }
    }

    function constructor(){
        if(isMovie()){            
            lib.osd(getId(), getYear());  
        }
    }
    return constructor;
})();

filmweb = (function(){
    var obj = this;

    function isMovie(){
        var filmType = document.getElementById('filmType').innerHTML;
        // 0 movie, 1 tv movie, 2 tv series
        return filmType < 2;
    }

    function getName(){
        // polish or original title if there is no polish one
        var title = document.getElementsByTagName('title')[0].text.match(/^(.+) \(\d{4}\) (- .+ )?- Filmweb$/)[1];
        var titleLen = title.length;
        var metas = document.getElementsByTagName('meta');
        obj = null;
        for (i = 0; i < metas.length; i ++) {
            obj = metas[i];
            if (obj.content.length >= titleLen) {
                if (obj.content == title) {
                    break;
                } else if (obj.content.substr(titleLen,  3) == ' / ') {
                    // original title exists
                    title = obj.content.match(/^.+ \/ (.+)$/)[1];
                    break;
                }
            }
        }
        // adding 'The' from back to front
        var theTitle = title.match(/^(.+), The$/);
        if (theTitle != null) {
            title = 'The ' + theTitle[1];
        }
        return title;
    }

    function getYear(){
        return document.getElementById('filmYear').innerHTML.match(/^ \((\d{4})\) (TV)?$/)[1];
//      return document.getElementsByTagName('title')[0].text.match(/^.+ \((\d{4})\) (- .+ )?- Filmweb$/)[1];
    }

    function constructor(){
        if(isMovie()){
            tmdb_api.MovieSearch(getName(), getYear());
        }
    }
    return constructor;
})();


// Start
(function(){
    factory = {
        "imdb.com" : imdb,
        "sharethe.tv" : sharethetv,
        "moviemeter.nl" : moviemeter,
        "whiwa.net" : whiwa,
        "trakt.tv" : trakt,
        "trailers.apple.com" : apple,
        "themoviedb.org" : tmdb,
        "allocine.fr" : allocine,
        "rottentomatoes.com" : rotten,
        "youtheater.com": youtheater,
        "sratim.co.il": youtheater,
        "filmweb.pl": filmweb
    };
    
    for (var i in factory){
        GM_log(i);
        if(location.href.indexOf(i) != -1){
            new factory[i]();
            break;
        }
    }
})();
