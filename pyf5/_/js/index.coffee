#if $.browser.msie
#    window.console =
#        log: (rest...) => null
#
#joinPath = (p1, p2) ->
#    path = [p1, p2].join '/'
#    path = path.replace /\/+/g, '/'
#
#
#FileModel = (data, project) ->
#
#    @name = ko.observable data['name']
#    @type = ko.observable data['type']
#    @absolutePath = ko.observable data['absolutePath']
#
#    @relativePath = ko.computed =>
#        relPath = @absolutePath().replace(project.path(), '')
#        relPath = relPath.substr(1) if relPath and relPath[0] == '/'
#
#    @url = ko.computed =>
#        "http://#{project.root.host()}/#{@relativePath()}"
#
#    @QRurl = ko.computed =>
#        "http://#{project.QRhost()}/#{@relativePath()}"
#
#    @isMuted = ko.computed =>
#        return false if not project.muteList().length
#
#        for mutePath in project.muteList()
#            return true if @absolutePath() == joinPath(project.path(), mutePath)
#        false
#
#    @mute = =>
#        if @relativePath() not in project.muteList()
#            project.muteList.push @relativePath()
#            project.save()
#
#    @unmute = =>
#        if @relativePath() in project.muteList()
#            project.muteList.remove @relativePath()
#            project.save()
#
#    @onClick = =>
#        if @type() is 'DIR'
#            project.currentFolder @relativePath()
#            return false
#        return true
#    @
#
#
#FolderSegment = (name, relativePath, project) ->
#    @name = ko.observable name
#    @relativePath = ko.observable relativePath
#
#    @onClick = =>
#        project.currentFolder @relativePath()
#    @
#
#
#ProjectModel = (data, root) ->
#    @root = root
#
#    # 和服务器对应的数据结构-----------------------------------------
#    @path = ko.observable ""
#    @active = ko.observable false
#    @active.subscribe (newValue) =>
#        console.log @path(), 'active', newValue
#        if newValue is true
#            for project in root.projects()
#                if project isnt @ and project.active()
#                    project.active(false)
#            if not @files().length
#                @currentFolder('')
#    @muteList = ko.observableArray []
#    @targetHost = ko.observable ''
#    @QRhost = ko.observable location.host
#    @compileLess = ko.observable false
#    @compileCoffee = ko.observable false
#    @delay = ko.observable 0.0
#    @delay.subscribe (newValue) =>
#        if parseFloat(newValue) isnt newValue
#            @delay(parseFloat(newValue))
#            @save()
#
#    # settings ---------------------------------------------
#    @showSettings = ko.observable $.cookie('hideSettings') != 'true'
#    @showSettings.subscribe (newValue) =>
#        $.cookie 'hideSettings', !newValue
#
#    @submitTargetHost = (item, event) =>
#        targetHost = $.trim $('#target-host-input').val()
#        if not targetHost
#            @clearTargetHost()
#        else if /^[\w\.:\-]+$/.exec targetHost
#            @targetHost targetHost
#            @save()
#        else
#            alert """请输入域名或ip地址（不带协议和路径）和端口，如：
#                  127.0.0.1:8080
#                  192.168.0.101
#                  domain.com:8080
#                  mysite.com"""
#            $('#target-host-input').val(targetHost).focus().select()
#
#    @clearTargetHost = (item, event) =>
#        @targetHost ""
#        $('#target-host-input').val ""
#        @save()
#
#    # file management -------------------------------------
#    @files = ko.observableArray []
#    @folderSegments = ko.observableArray []
#
#    @currentFolder = ko.observable ''
#    @currentFolder.subscribe (relativePath) =>
#        if @active()
#            @folderSegments.removeAll()
#            parts = relativePath.split('/')
#            relativeParts = []
#            for part in parts
#                relativeParts.push part
#                if part
#                    @folderSegments.push(new FolderSegment(part, relativeParts.join('/'), @))
#            @queryFileList joinPath(@path(), relativePath)
#    @currentFolder.extend notify:'always'  # 不论是否有修改，都发生subscribe
#
#    @goRoot = ->
#        @currentFolder ''
#
#    @queryFileList = (path) ->
#        @files.removeAll()
#
#        API.os.listDir path, (data) =>
#            @files.removeAll()
#            for fileData in data['list']
#                @files.push(new FileModel(fileData, @))
#            $('.file-list td.op a').tooltip()
#
#    # QRCode --------------------------------------------
#    @QRhost.subscribe (newValue) =>
#        setTimeout(
#            => @QRUrlChange()
#            100
#        )
#
#    @QRCodeFile = ko.observable null
#    @QRCodeFile.extend notify:'always'
#    @QRCodeFile.subscribe (newValue) =>
#        if newValue
#            $('#qrcode-modal')
#                .modal()
#            root.updateQRCode newValue.QRurl()
#
#    @QRUrlChange = (item, event) =>
#        text = $('#qrurl-input').val()
#        root.updateQRCode text
#
#    @showQRCode = (item, event) =>
#        @QRCodeFile item
#
#    # event handlers
#    @onClick = (item, event) =>
#        prevActiveProject = root.activeProject()
#        if prevActiveProject
#            prevActiveProject.active(false)
#            prevActiveProject.save()
#        @active(true)
#        @save()
#
#    @onCompileCheckboxClick = (item, event) =>
#        if event.target.tagName.toLowerCase() == 'label'
#            setTimeout @save, 100
#        return true
#
#    # save/load/export ----------------------------------
#    @load = (data) =>
#        @path(data.path)
#        @active(!!data.active)
#        @muteList(data.muteList or [])
#        @targetHost(data.targetHost or "")
#        @QRhost(data.QRhost or root.host())
#        @compileLess(!!data.compileLess)
#        @compileCoffee(!!data.compileCoffee)
#        @delay(parseFloat(data.delay) || 0.0)
#
#    @save = =>
#        API.project.update @
#
#    @export = =>
#        path: @path()
#        active: @active()
#        muteList: @muteList()
#        targetHost: @targetHost()
#        QRhost: @QRhost()
#        compileLess: @compileLess()
#        compileCoffee: @compileCoffee()
#        delay: parseFloat @delay()
#
#    @load(data) if data
#    @
#
#
#ViewModel = ->
#    @host = ko.observable location.host
#
#    @localHosts = ko.observableArray ['127.0.0.1']
#
#    @projects = ko.observableArray []
#    @projects.subscribe (newValue) =>
#        setTimeout(
#            => $('.project-box table .op a').tooltip()
#            500)
#
#    @activeProject = ko.computed =>
#        for project in @projects()
#            return project if project.active()
#    @activeProject.subscribe (project) =>
#        setTimeout(
#            => $('.project-box [data-toggle=tooltip]').tooltip()
#            500)
#
#    @queryLocalHosts = =>
#        API.os.localHosts (resp) =>
#            @localHosts resp.hosts
#
#    @findProject = (path) =>
#        for project in @projects()
#            return project if project.path() == path
#
#    @loadProjectData = (projectData) =>
#        project = @findProject projectData.path
#        if project
#            project.load projectData
#        else
#            project = new ProjectModel projectData, @
#            @projects.push project
#        project
#
#    @queryProjects = =>
#        API.project.list (data) =>
#            for projectData in data['projects']
#                @loadProjectData projectData
#
#    @removeProject = (project) =>
#        @projects.remove project
#        API.project.remove project.path()
#
#    @addProjectWithPath = (path) =>
#        API.project.add path, (resp) =>
#            @loadProjectData resp.project
#            if @projects().length == 1
#                @projects().active(true)
#            $('#new-path-input').val ''
#
#    @askRemoveProject = (project, event) =>
#        @removeProject(project) if confirm '是否确认【删除】该项目?'
#        event.stopImmediatePropagation()
#
#    @onSubmitProjectPath = (formElement) =>
#        $input = $ '#new-path-input'
#        projectPath = $.trim $input.val()
#        $input.val projectPath
#
#        if projectPath
#            @addProjectWithPath projectPath
#        else
#            alert '请输入路径'
#
#    @updateQRCode = (text) =>
#        $el = $ '#qrcode'
#
#        if not @qrcode
#            @qrcode = new QRCode $el[0], {
#                width:$el.width()
#                height:$el.height()
#                text: ''
#            }
#        @qrcode.makeCode text or ''
#
#    @queryLocalHosts()
#    @queryProjects()
#
#    @
#
#
#$ =>
#    window.vm = new ViewModel()
#    ko.applyBindings vm
#
#    API.os.f5Version (resp) =>
#        $.getScript("http://www.getf5.com/update.js?ver=#{resp.version}") if resp.status == 'ok'
#
#    `
#    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
#        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
#        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
#    })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
#    `
#    ga 'create', 'UA-22253493-9', '127.0.0.1'
#    ga 'send', 'pageview'



libs = [ 'underscore', 'angular',
    'ngRoute',
    'mgcrea.ngStrap'

    'services/api',

    'controllers/IndexController',
    'controllers/FilesController',
    'controllers/SettingsController',

    'directives/project'
]
main = (_, angular) ->
    index = angular.module 'index', ['ngRoute', 'mgcrea.ngStrap', 'app']

    index.run (api) ->
        console.log 'run'

    angular.element(document).ready ->
        console.log 'ready'
        angular.bootstrap(document, ['index'])


require ['/_/js/config.js'], ->
    require libs, main