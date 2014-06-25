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


getFileName = (path) ->
    return '' if not path
    return path.replace(/\?.*$/, '').replace(/^.*\//, '')


getFileExtension = (path) ->
    base = getFileName(path);
    matched = base.match(/\.[^.]+$/);
    return if matched then matched[0].toLowerCase() else '';


equals = (url, path) ->
    return url and path and getFileName(url) == getFileName(path)


bustCache = (url) ->
    pattern = /_f5=[\d\.]+/
    replacement = "_f5=#{Math.random()}"

    console.log 'bustCache', url
    if pattern.test(url)
        url = url.replace(pattern, replacement)
    else if '?' in url
        url += ('&' + replacement)
    else
        url += ('?' + replacement)
    console.log 'bustCache', '->', url
    return url


F5 = ->
    API_ROOT = do ->
        scripts = document.getElementsByTagName 'script'
        for script in scripts
            src = script.src
            if src.indexOf('/_f5.js') > -1
                console.log 'apiRootUrl', "http://#{parseUri(src).hostname}/_/"
                return "http://#{parseUri(src).hostname}/_/"
        return '/'
    MAX_RETRY = 3

    retryCount = 0

    reload = ->
        location.reload(true)

    applyChange = (path, type) ->
        return if type not in ['modified', 'created']

        ext = getFileExtension(path)
        if ext in ['.css']
            updateCSS(path)
        else if ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
            updateImage(path)
        else if ext in ['.js']
            updateScript(path)
        else
            reload()

    findStyleSheet = (name) ->
        for ss in document.styleSheets
            if equals(ss.href, name)
                return ss
            else
                if ss.cssText and ss.cssText.indexOf(name) > 0
                    return ss
                else
                    for rule in (ss.rules or [])
                        if equals(rule.href, name)
                            return ss
        return null

    reattachStyleSheet = (styleSheet) ->
        node = styleSheet?.ownerNode or styleSheet?.owningElement

        if node?.href
            link = document.createElement 'link'
            link.href = bustCache(node.href)
            link.rel = 'stylesheet'

            node.parentElement.appendChild(link)
            setTimeout ->
                node.parentElement.removeChild(node)
            , 500

    updateCSS = (path) ->
        styleSheet = findStyleSheet(getFileName(path))
        reattachStyleSheet(styleSheet)

    updateImage = (path) ->
        for image in document.images
            if equals(image.src, path)
                image.src = bustCache(image.src)

        for ss in document.styleSheets
            reattachStyleSheet(ss)  # todo: improve performance

    updateScript = (path) ->
        for script in document.scripts
            if equals(script.src, path)
                reload()

    @handleChanges = (resp) =>
        retryCount = 0
        setCookie('_f5_reply_time', resp.time)

        for path, info of resp.changes
            applyChange(path, info.type)

        console.log 'handleChanges', resp.changes
        setTimeout =>
            @queryChanges()
        , 100

    @queryChanges = ->
        url = "#{API_ROOT}changes?callback=_F5.handleChanges"

        lastChangeTime = parseFloat(getCookie('_f5_reply_time', -Math.random()))
        if lastChangeTime
            url += "&qt=#{lastChangeTime}"

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
, 500
