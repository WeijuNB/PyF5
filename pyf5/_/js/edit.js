var URL = window.URL || window.webkitURL || window.mozURL || window.msURL;
navigator.saveBlob = navigator.saveBlob || navigator.msSaveBlob || navigator.mozSaveBlob || navigator.webkitSaveBlob;
window.saveAs = window.saveAs || window.webkitSaveAs || window.mozSaveAs || window.msSaveAs;

// Because highlight.js is a bit awkward at times
var languageOverrides = {
    js: 'javascript',
    html: 'xml'
};

marked.setOptions({
    highlight: function(code, lang){
        if(languageOverrides[lang]) lang = languageOverrides[lang];
        return hljs.LANGUAGES[lang] ? hljs.highlight(lang, code).value : code;
    }
});

function EditorViewModel(absolutePath) {
    var self = this;

    self.editor = CodeMirror.fromTextArea(document.getElementById('code'), {
        mode: 'gfm',
        lineNumbers: true,
        matchBrackets: true,
        lineWrapping: true,
        theme: 'default',
        onChange: function(e) {
            self.currentContent(e.getValue());
            console.log(e);
        }
    });
    self.editor.focus();

    self.absolutePath = ko.observable(null);
    self.originalContent = ko.observable(self.editor.getValue());
    self.currentContent = ko.observable(self.editor.getValue());
    self.currentOutput = ko.computed(function(){
        var code = self.currentContent().replace(/<equation>((.*?\n)*?.*?)<\/equation>/ig, function(a, b){
            return '<img src="http://latex.codecogs.com/png.latex?' + encodeURIComponent(b) + '" />';
        });
        return marked(code);
    });
    self.changed = ko.computed(function(){
        return self.currentContent() == self.originalContent();
    });

    self.save = function() {
        var code = self.editor.getValue();
        API.os.writeFile(window.absolutePath, code, function(data) {
            self.originalContent(code);
        });
    }
}

var vm = new EditorViewModel(absolutePath);
ko.applyBindings(vm);


document.addEventListener('keydown', function(e){
    if(e.keyCode == 83 && (e.ctrlKey || e.metaKey)){
        e.preventDefault();
        vm.save();
        return false;
    }
});



