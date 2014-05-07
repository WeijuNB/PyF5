if not window.console
    window.console =
        debug: ->
        log: ->
        info: ->
        warn: ->
        error: ->

getScript = (url, errorCallback) ->
    script = document.createElement 'script'
    done = false

    script.async = true
    script.defer = true
    script.src = url

    if typeof errorCallback == 'function'
        script.onerror = (e) -> errorCallback(url: url, event: e)

    script.onload = script.onreadystatechange = ->
        if not done and (not this.readyState or @readyState in ['loaded', 'complete'])
            done = true
            script.onload = script.onreadystatechange = null
            if script?.parentNode
                script.parentNode.removeChild script

    parent = document.getElementsByTagName('body');
    if parent.length == 0
        parent = document.getElementsByTagName('head')

    if parent.length
        parent[0].appendChild script


parseUri = (url) ->
    a = document.createElement 'a'
    a.href = url
    return a


setCookie = (name, value) ->
    if name
        if value == undefined
            document.cookie = "#{name}=;path=/;expires=Thu, 01 Jan 1970 00:00:00 GMT"
        else
            document.cookie = "#{name}=#{value};path=/"


getCookie = (name, defaultValue) ->
    cookieArray = document.cookie.split('; ')
    for cookie in cookieArray
        i = cookie.indexOf('=')
        if i > 0
            if name == cookie.substring(0, i)
                return cookie.substring(i + 1)
    return defaultValue or null


getExt = (path) ->
    i = path.lastIndexOf('/')
    return '' if i < 0

    name = path.substring(i)
    li = /(\.[^\.\/\?&]+)[^\/]*$/.exec(name)
    if li?.length
        return li[1]
    return ''

getFileName = (path) ->
    i = path.lastIndexOf('/')
    return '' if i < 0

    name = path.substring(i)
    li = /([^\/\?&]+)[^\/]*$/.exec(name)
    if li.length
        return li[1]
    return ''


bustCache = (url) ->
    pattern = /_f5=[\d\.]+/
    replacement = "_f5=#{Math.random()}"

    console.debug 'bustCache', url
    if pattern.test(url)
        url = url.replace(pattern, replacement)
    else if '?' in url
        url += ('&' + replacement)
    else
        url += ('?' + replacement)
    console.debug 'bustCache', '->', url
    return url


F5 = ->
    API_ROOT = do ->
        scripts = document.getElementsByTagName 'script'
        for script in scripts
            src = script.src
            if src.indexOf('/_f5.js') > -1
                console.debug 'apiRootUrl', "http://#{parseUri(src).hostname}/_/"
                return "http://#{parseUri(src).hostname}/_/"
        return '/'
    MAX_RETRY = 3

    retryCount = 0

    applyChange = (path, type) ->
        return if type not in ['modified', 'created']

        ext = getExt(path)
        if ext in ['.css']
            updateCSS(path)



    updateCSS = (path) ->
        for element in document.getElementsByTagName 'link'
            href = element.href
            ext = getExt(href)
            console.debug 'files', getFileName(href), getFileName(path)
            if ext in ['.css'] and getFileName(href) == getFileName(path)
                element.href = bustCache(element.href)
                console.debug 'updateCSS', element.href
                break


    @handleChanges = (resp) =>
        retryCount = 0
        changeTime = -Math.random()

        for path, info of resp.changes
            if info.time > changeTime
                changeTime = info.time
            applyChange(path, info.type)

        setCookie('_f5_ct', changeTime)

        console.log 'handleChanges', resp.changes
        setTimeout =>
            @queryChanges()
        , 100

    @queryChanges = ->
        lastChangeTime = parseFloat(getCookie('_f5_ct', -Math.random()))
        url = "#{API_ROOT}changes?callback=_F5.handleChanges&qt=#{lastChangeTime}"
        getScript url, =>
            retryCount += 1
            if retryCount >= MAX_RETRY
                alert '和 [F5] 失联，停止自动刷新'
            else
                setTimeout =>
                    @queryChanges()
                , 3000

    @


window._F5 = new F5()
setTimeout ->
    window._F5.queryChanges()
, 1000
