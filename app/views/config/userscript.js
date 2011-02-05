# -*- coding: utf-8 -*-
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
// @include     http://trakt.tv/movie/*
// @include     http://*.trak.tv/movie/*
// @include     http://trailers.apple.com/trailers/*
// @include     http://www.themoviedb.org/movie/*
// @exclude     http://trak.tv/movie/*/*
// @exclude     http://*.trak.tv/movie/*/*
// ==/UserScript==

var version = 6;

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
        return 'tt' + location.href.replace(/[^\d+]+/g, '');
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
        return imdb_id;
        
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
        return imdb_id;
        
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
        return imdb_id;
        
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
        return imdb_input.value.substr(2);
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
     *  AJAX post and call 'callback' function
     */
    function post(newurl, callback) {
        GM_xmlhttpRequest({
            method: 'GET',
            url: newurl,
            headers: {
            'User-agent': 'Mozilla/4.0 (compatible) Greasemonkey',
            'Accept': 'application/atom+xml,application/xml,text/xml',
            },
            onload: function(responseDetails) {
                callback(responseDetails);
            }
        });
    }

    /*
     *  Search TheMovieDB for IMDB ID, year of release and open OSD
     *
     */
    function getId(response) {
        if (!response) {
            var TMDB_API_KEY = "31582644f51aa19f8fcd9b2998e17a9d"

            var mName = document.title.substr(0, document.title.indexOf(" -")).replace(/ /g, "+");
            var url = 'http://api.themoviedb.org/2.1/Movie.search/en/xml/' + TMDB_API_KEY + '/' + mName;
    
            post(url, getId)
        } else {
            if (!response.responseXML) {
                response.responseXML = new DOMParser().parseFromString(response.responseText, "text/xml");
            }

            var imdb_id = response.responseXML.getElementsByTagName('imdb_id')[0].firstChild.nodeValue; 

            var year = getYear(response.responseXML);
        }

        // This is here since getId is called asyncronously from ajax call
        lib.osd(imdb_id, year);    
    }

    /*
     *  Gets year of release. First tries to get it from TMDB response.
     *  If that fails, gets the year from page copyright notice.
     *
     */
    function getYear(xml){
        var year;
        if (xml) {
            year = xml.getElementsByTagName('released')[0].firstChild;
            if (year != null) {
                year = year.data;
                year = year.substr(0, 4);
            } else {
                year = getYearFromPage();
            }
        } else {
            year = getYearFromPage();
        }

        return year;
    }

    /*
     *  Retrieves year from movie copyright notice.
     *
     */ 
    function getYearFromPage() {
        var fullReleaseDate = document.getElementById("view-showtimes").parentNode.innerHTML;
        var justYear = fullReleaseDate.substr(fullReleaseDate.indexOf("Copyright", 0)+12, 4);

        return justYear;
    }

    function constructor(){
        if (window.navigator.userAgent.indexOf("Chrome") < 0) {
            if(isMovie()){
                // lib.osd will be called by AJAX request in getId()
                getId();    
            }
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
     *      AJAX post and call 'callback' function
     */
    function post(newurl, callback) {
        GM_xmlhttpRequest({
            method: 'GET',
            url: newurl,
            headers: {
               'User-agent': 'Mozilla/4.0 (compatible) Greasemonkey',
               'Accept': 'application/atom+xml,application/xml,text/xml',
            },
            onload: function(responseDetails) {
               callback(responseDetails);
            }
        });
    }

    /*
     *      Search TheMovieDB for IMDB ID, year of release and open OSD
     *
     */
    function getId(response) {
        if (!response) {
            var TMDB_API_KEY = "31582644f51aa19f8fcd9b2998e17a9d"

            mName = document.title.substr(0, document.title.indexOf("TMDb")-3).replace(/ /g, "+");
            mName = mName.replace(/·/g, "-");

            var url = 'http://api.themoviedb.org/2.1/Movie.search/en/xml/' + TMDB_API_KEY + '/' + mName;

            post(url, getId);
        } else {
            if (!response.responseXML) {
                response.responseXML = new DOMParser().parseFromString(response.responseText, "text/xml");
            }

            var imdb_id = response.responseXML.getElementsByTagName('imdb_id')[0].firstChild.nodeValue; 
            var year = getYear();
                
            // This is here since getId is called asyncronously from ajax call
            lib.osd(imdb_id, year);    
        }
    }
    
    function getYear(){
        var year = document.getElementById("year").innerHTML;
        year = year.substr(1, year.length-2);
        return year;
    }
    
    function constructor(){
        if (window.navigator.userAgent.indexOf("Chrome") < 0) {
            if(isMovie()){
                getId();    
            }
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
        "themoviedb.org" : tmdb
    };
    for (var i in factory){
        GM_log(i);
        if(location.href.indexOf(i) != -1){
            new factory[i]();
            break;
        }
    }
})();
