joinPath = (p1, p2) ->
    path = [p1, p2].join '/'
    path = path.replace /\/+/g, '/'


FileModel = (data, project) ->

    @name = ko.observable data['name']
    @type = ko.observable data['type']
    @absolutePath = ko.observable data['absolutePath']

    @relativePath = ko.computed () =>
        relPath = @absolutePath().replace(project.path(), '')
        relPath = relPath.substr(1) if relPath and relPath[0] == '/'

    @url = ko.computed () =>
        root = project.root
        if root.port()
            "http://#{project.activeDomain()}:#{root.port()}/#{@relativePath()}"
        else
            "http://#{project.activeDomain()}/#{@relativePath()}"

    @isMuted = ko.computed () =>
        false if not project.muteList()

        for mutePath in project.muteList()
            true if @absolutePath() == joinPath project.path(), mutePath
        false

    @mute = =>
        if @relativePath() not in project.muteList()
            project.muteList.push @relativePath()
            project.save()

    @unmute = =>
        if @relativePath() in project.muteList()
            project.muteList.remove @relativepath()
            project.save()

    @onClick = =>
        if @type() is 'DIR'
            project.currentFolder @relativePath()
            false
        true
    @


FolderSegment = (name, relativePath, project) ->
    @name = ko.observable name
    @relativePath = ko.observable relativePath

    @onClick = =>
        project.currentFolder @relativePath()
    @


ProjectModel = (data, root) ->
    @root = root

    # 和服务器对应的数据结构-----------------------------------------
    @path = ko.observable ""
    @active = ko.observable false
    @muteList = ko.observableArray []
    @targetHost = ko.observable ''
    @domains = ko.observableArray []
    @activeDomain = ko.observable '127.0.0.1'

    # 域名切换相关--------------------------------------------------
    @activeDomains = ko.observableArray ['127.0.0.1']
    @activeDomains.subscribe (newValue) =>
        @activeDomain newValue[0]
        setTimeout @save, 100  # 这里的save会和其他save冲突，导致后发先至引起数据错乱，所以暂时丑陋地解决一下
        @QRCodeFile @QRCodeFile()

    @allHosts = ko.computed =>
        @domains().concat root.localHosts()

    @activeDomainAndPort = ko.computed =>
        if root.port()
            "#{@activeDomain()}:#{root.port()}"
        else
            @activeDomain()

    @clickAddDomain = (item, event) =>
        domain = $.trim prompt('请输入想要添加的域名：')
        if domainf
            if not /^[\w\.\-]+$/.exec domain
                alert '格式不对吧'
            else
                if domain in @omains
                    alert '域名已存在'
                else
                    @domains.unshift domain
                    @activeDomains [domain]

    @clickRemoveDomain = (item, event) =>
        @domains.remove @activeDomain()
        if @activeHosts().length
            @activeDomains [@allHosts()[0]]

    # settings ---------------------------------------------
    @showSettings = ko.observable $.cookie('hideSettings') != 'true'
    @showSettings.subscribe (newValue) =>
        $.cookie 'hideSettings', !newValue

    @submitTargetHost = (item, event) =>
        targetHost = $.trim $('#target-host-input').val()
        if not targetHost
            @clearTargetHost()
        else if /^[\w\.:\-]+$/.exec targetHost
            @targetHost targetHost
            @save()
        else
            alert """请输入域名或ip地址（不带协议和路径）和端口，如：
                  127.0.0.1:8080
                  192.168.0.101
                  domain.com:8080
                  mysite.com"""
            $('#target-host-input').val(targetHost).focus().select()

    @clearTargetHost = (item, event) =>
        @targetHost ""
        $('#target-host-input').val ""
        @save()

    # file management -------------------------------------
    @files = ko.observableArray []
    @folderSegments = ko.observableArray []

    @currentFolder = ko.observable ''
    @currentFolder.subscribe (relativePath) =>
        @folderSegments.removeAll()
        parts = relativePath.split('/')
        relativeParts = []
        for part in parts
            relativeParts.push part
            if part
                @folderSegments.push(new FolderSegment(part, relativeParts.join('/'), @))
        @queryFileList joinPath(@path(), relativePath)
    @currentFolder.extend notify:'always'  # 不论是否有修改，都发生subscribe

    @goRoot = ->
        @currentFolder ''

    @queryFileList = (path) ->
        @files.removeAll()

        API.os.listDir path, (data) =>
            @files.removeAll()
            for fileData in data['list']
                @files.push(new FileModel(fileData, @))
            $('#file-list td.op a').tooltip()

    # QRCode --------------------------------------------
    @QRCodeFile = ko.observable null
    @QRCodeFile.extend notify:'always'
    @QRCodeFile.subscribe (newValue) =>
        if newValue
            $('#qrcode-modal')
                .modal()
                .on 'hidden', () =>
                    @QRCodeFile(null)
            @updateQRCode newValue.url()

    @QRUrlChange = (item, event) =>
        @updateQRCode $(event.target).val()

    @updateQRCode = (text) ->
        $el = $('#qrcode')
        $el.empty().qrcode(
            width:$el.width(),
            height:$el.height(),
            text:text
        )

    @showQRCode = (item, event) ->
        @QRCodeFile item

    # save/load/export ----------------------------------
    @load = (data) =>
        @path data.path
        @active(data.active? or false)
        @muteList(data.muteList or [])
        @targetHost(data.targetHost or "")
        @domains(data.domains or [])
        @activeDomain(data.activeDomain or '127.0.0.1')
        @activeDomains([@activeDomain()])

    @save = =>
        API.project.update @

    @export = =>
        path: @path()
        active: @active()
        muteList: @muteList()
        targetHost: @targetHost()
        domains: @domains()
        activeDomain: @activeDomain()

    @load(data) if data
    @


ViewModel = ->
    @port = ko.observable location.port

    @localHosts = ko.observableArray ['127.0.0.1']

    @projects = ko.observableArray []
    @projects.subscribe (newValue) =>
        setTimeout(
            => $('#projects .op a').tooltip()
            500)

    @activeProject = ko.observable null
    @activeProject.subscribe (project) =>
        if project
            if not project.active()
                project.active true
                project.save()
            if not project.files().length
                project.currentFolder ''
        for _project in @projects()
            if _project and _project != project and _project.active()
                _project.active false
                _project.save()
        setTimeout(
            => $('#project [data-toggle=tooltip]').tooltip()
            500)

    @queryLocalHosts = =>
        API.os.localHosts (resp) =>
            @localHosts resp.hosts

    @findProject = (path) =>
        for project in @projects()
            return project if project.path() == path

    @loadProjectData = (projectData) =>
        project = @findProject projectData.path
        if project
            project.load projectData
        else
            project = new ProjectModel projectData, @
            @projects.push project
        project

    @queryProjects = =>
        API.project.list (data) =>
            for projectData in data['projects']
                project = @loadProjectData projectData
                @activeProject(project) if project.active() and project != @activeProject()

    @removeProject = (project) =>
        @projects.remove project
        API.project.remove project.path()
        @activeProject(null) if @activeProject() == project

    @addProjectWithPath = (path) =>
        API.project.add path, (resp) =>
            @loadProjectData resp.project
            @activeProject(@projects()[0]) if @projects().length == 1 and not @activeProject()
            $('#new-path-input').val ''

    @onSelectProject = (project) =>
        @activeProject project

    @askRemoveProject = (project) =>
        @removeProject(project) if confirm '是否确认【删除】该项目?'

    @onSubmitProjectPath = (formElement) =>
        $input = $ '#new-path-input'
        projectPath = $.trim $input.val()
        $input.val projectPath

        if projectPath
            @addProjectWithPath projectPath
        else
            alert '请输入路径'

    @queryLocalHosts()
    @queryProjects()
    @


$ =>
    window.vm = new ViewModel()
    ko.applyBindings vm

    API.os.f5Version (resp) =>
        $.getScript("http://www.getf5.com/update.js?ver=#{resp.version}") if resp.status == 'ok'

    `
    (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
        (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
        m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
    })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
    `
    ga 'create', 'UA-22253493-9', '127.0.0.1'
    ga 'send', 'pageview'
