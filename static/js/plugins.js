Array.prototype.unique = function(){
    var n = {},r=[]; //n为hash表，r为临时数组
    for(var i = 0; i < this.length; i++) //遍历当前数组
    {
        if (!n[this[i]]) //如果hash表中没有当前项
        {
            n[this[i]] = true; //存入hash表
            r.push(this[i]); //把当前数组的当前项push到临时数组里面
        }
    }
    return r;
};

function urlincode(obj){
  var str = "?"
  var num = 0;
  for(var o in obj){
    num==0?(str+=o+"="+obj[o]):(str+="&"+o+"="+obj[o]);
    num++;
  }
  return str;
}

/*!
 * jQuery Form Plugin
 * version: 3.51.0-2014.06.20
 * Requires jQuery v1.5 or later
 * Copyright (c) 2014 M. Alsup
 * Examples and documentation at: http://malsup.com/jquery/form/
 * Project repository: https://github.com/malsup/form
 * Dual licensed under the MIT and GPL licenses.
 * https://github.com/malsup/form#copyright-and-license
 */
/*global ActiveXObject */

// AMD support
(function (factory) {
    "use strict";
    if (typeof define === 'function' && define.amd) {
        // using AMD; register as anon module
        define(['jquery'], factory);
    } else {
        // no AMD; invoke directly
        factory( (typeof(jQuery) != 'undefined') ? jQuery : window.Zepto );
    }
}

(function($) {
"use strict";

/*
    Usage Note:
    -----------
    Do not use both ajaxSubmit and ajaxForm on the same form.  These
    functions are mutually exclusive.  Use ajaxSubmit if you want
    to bind your own submit handler to the form.  For example,

    $(document).ready(function() {
        $('#myForm').on('submit', function(e) {
            e.preventDefault(); // <-- important
            $(this).ajaxSubmit({
                target: '#output'
            });
        });
    });

    Use ajaxForm when you want the plugin to manage all the event binding
    for you.  For example,

    $(document).ready(function() {
        $('#myForm').ajaxForm({
            target: '#output'
        });
    });

    You can also use ajaxForm with delegation (requires jQuery v1.7+), so the
    form does not have to exist when you invoke ajaxForm:

    $('#myForm').ajaxForm({
        delegation: true,
        target: '#output'
    });

    When using ajaxForm, the ajaxSubmit function will be invoked for you
    at the appropriate time.
*/

/**
 * Feature detection
 */
var feature = {};
feature.fileapi = $("<input type='file'/>").get(0).files !== undefined;
feature.formdata = window.FormData !== undefined;

var hasProp = !!$.fn.prop;

// attr2 uses prop when it can but checks the return type for
// an expected string.  this accounts for the case where a form 
// contains inputs with names like "action" or "method"; in those
// cases "prop" returns the element
$.fn.attr2 = function() {
    if ( ! hasProp ) {
        return this.attr.apply(this, arguments);
    }
    var val = this.prop.apply(this, arguments);
    if ( ( val && val.jquery ) || typeof val === 'string' ) {
        return val;
    }
    return this.attr.apply(this, arguments);
};

/**
 * ajaxSubmit() provides a mechanism for immediately submitting
 * an HTML form using AJAX.
 */
$.fn.ajaxSubmit = function(options) {
    /*jshint scripturl:true */

    // fast fail if nothing selected (http://dev.jquery.com/ticket/2752)
    if (!this.length) {
        log('ajaxSubmit: skipping submit process - no element selected');
        return this;
    }

    var method, action, url, $form = this;

    if (typeof options == 'function') {
        options = { success: options };
    }
    else if ( options === undefined ) {
        options = {};
    }

    method = options.type || this.attr2('method');
    action = options.url  || this.attr2('action');

    url = (typeof action === 'string') ? $.trim(action) : '';
    url = url || window.location.href || '';
    if (url) {
        // clean url (don't include hash vaue)
        url = (url.match(/^([^#]+)/)||[])[1];
    }

    options = $.extend(true, {
        url:  url,
        success: $.ajaxSettings.success,
        type: method || $.ajaxSettings.type,
        iframeSrc: /^https/i.test(window.location.href || '') ? 'javascript:false' : 'about:blank'
    }, options);

    // hook for manipulating the form data before it is extracted;
    // convenient for use with rich editors like tinyMCE or FCKEditor
    var veto = {};
    this.trigger('form-pre-serialize', [this, options, veto]);
    if (veto.veto) {
        log('ajaxSubmit: submit vetoed via form-pre-serialize trigger');
        return this;
    }

    // provide opportunity to alter form data before it is serialized
    if (options.beforeSerialize && options.beforeSerialize(this, options) === false) {
        log('ajaxSubmit: submit aborted via beforeSerialize callback');
        return this;
    }

    var traditional = options.traditional;
    if ( traditional === undefined ) {
        traditional = $.ajaxSettings.traditional;
    }

    var elements = [];
    var qx, a = this.formToArray(options.semantic, elements);
    if (options.data) {
        options.extraData = options.data;
        qx = $.param(options.data, traditional);
    }

    // give pre-submit callback an opportunity to abort the submit
    if (options.beforeSubmit && options.beforeSubmit(a, this, options) === false) {
        log('ajaxSubmit: submit aborted via beforeSubmit callback');
        return this;
    }

    // fire vetoable 'validate' event
    this.trigger('form-submit-validate', [a, this, options, veto]);
    if (veto.veto) {
        log('ajaxSubmit: submit vetoed via form-submit-validate trigger');
        return this;
    }

    var q = $.param(a, traditional);
    if (qx) {
        q = ( q ? (q + '&' + qx) : qx );
    }
    if (options.type.toUpperCase() == 'GET') {
        options.url += (options.url.indexOf('?') >= 0 ? '&' : '?') + q;
        options.data = null;  // data is null for 'get'
    }
    else {
        options.data = q; // data is the query string for 'post'
    }

    var callbacks = [];
    if (options.resetForm) {
        callbacks.push(function() { $form.resetForm(); });
    }
    if (options.clearForm) {
        callbacks.push(function() { $form.clearForm(options.includeHidden); });
    }

    // perform a load on the target only if dataType is not provided
    if (!options.dataType && options.target) {
        var oldSuccess = options.success || function(){};
        callbacks.push(function(data) {
            var fn = options.replaceTarget ? 'replaceWith' : 'html';
            $(options.target)[fn](data).each(oldSuccess, arguments);
        });
    }
    else if (options.success) {
        callbacks.push(options.success);
    }

    options.success = function(data, status, xhr) { // jQuery 1.4+ passes xhr as 3rd arg
        var context = options.context || this ;    // jQuery 1.4+ supports scope context
        for (var i=0, max=callbacks.length; i < max; i++) {
            callbacks[i].apply(context, [data, status, xhr || $form, $form]);
        }
    };

    if (options.error) {
        var oldError = options.error;
        options.error = function(xhr, status, error) {
            var context = options.context || this;
            oldError.apply(context, [xhr, status, error, $form]);
        };
    }

     if (options.complete) {
        var oldComplete = options.complete;
        options.complete = function(xhr, status) {
            var context = options.context || this;
            oldComplete.apply(context, [xhr, status, $form]);
        };
    }

    // are there files to upload?

    // [value] (issue #113), also see comment:
    // https://github.com/malsup/form/commit/588306aedba1de01388032d5f42a60159eea9228#commitcomment-2180219
    var fileInputs = $('input[type=file]:enabled', this).filter(function() { return $(this).val() !== ''; });

    var hasFileInputs = fileInputs.length > 0;
    var mp = 'multipart/form-data';
    var multipart = ($form.attr('enctype') == mp || $form.attr('encoding') == mp);

    var fileAPI = feature.fileapi && feature.formdata;
    log("fileAPI :" + fileAPI);
    var shouldUseFrame = (hasFileInputs || multipart) && !fileAPI;

    var jqxhr;

    // options.iframe allows user to force iframe mode
    // 06-NOV-09: now defaulting to iframe mode if file input is detected
    if (options.iframe !== false && (options.iframe || shouldUseFrame)) {
        // hack to fix Safari hang (thanks to Tim Molendijk for this)
        // see:  http://groups.google.com/group/jquery-dev/browse_thread/thread/36395b7ab510dd5d
        if (options.closeKeepAlive) {
            $.get(options.closeKeepAlive, function() {
                jqxhr = fileUploadIframe(a);
            });
        }
        else {
            jqxhr = fileUploadIframe(a);
        }
    }
    else if ((hasFileInputs || multipart) && fileAPI) {
        jqxhr = fileUploadXhr(a);
    }
    else {
        jqxhr = $.ajax(options);
    }

    $form.removeData('jqxhr').data('jqxhr', jqxhr);

    // clear element array
    for (var k=0; k < elements.length; k++) {
        elements[k] = null;
    }

    // fire 'notify' event
    this.trigger('form-submit-notify', [this, options]);
    return this;

    // utility fn for deep serialization
    function deepSerialize(extraData){
        var serialized = $.param(extraData, options.traditional).split('&');
        var len = serialized.length;
        var result = [];
        var i, part;
        for (i=0; i < len; i++) {
            // #252; undo param space replacement
            serialized[i] = serialized[i].replace(/\+/g,' ');
            part = serialized[i].split('=');
            // #278; use array instead of object storage, favoring array serializations
            result.push([decodeURIComponent(part[0]), decodeURIComponent(part[1])]);
        }
        return result;
    }

     // XMLHttpRequest Level 2 file uploads (big hat tip to francois2metz)
    function fileUploadXhr(a) {
        var formdata = new FormData();

        for (var i=0; i < a.length; i++) {
            formdata.append(a[i].name, a[i].value);
        }

        if (options.extraData) {
            var serializedData = deepSerialize(options.extraData);
            for (i=0; i < serializedData.length; i++) {
                if (serializedData[i]) {
                    formdata.append(serializedData[i][0], serializedData[i][1]);
                }
            }
        }

        options.data = null;

        var s = $.extend(true, {}, $.ajaxSettings, options, {
            contentType: false,
            processData: false,
            cache: false,
            type: method || 'POST'
        });

        if (options.uploadProgress) {
            // workaround because jqXHR does not expose upload property
            s.xhr = function() {
                var xhr = $.ajaxSettings.xhr();
                if (xhr.upload) {
                    xhr.upload.addEventListener('progress', function(event) {
                        var percent = 0;
                        var position = event.loaded || event.position; /*event.position is deprecated*/
                        var total = event.total;
                        if (event.lengthComputable) {
                            percent = Math.ceil(position / total * 100);
                        }
                        options.uploadProgress(event, position, total, percent);
                    }, false);
                }
                return xhr;
            };
        }

        s.data = null;
        var beforeSend = s.beforeSend;
        s.beforeSend = function(xhr, o) {
            //Send FormData() provided by user
            if (options.formData) {
                o.data = options.formData;
            }
            else {
                o.data = formdata;
            }
            if(beforeSend) {
                beforeSend.call(this, xhr, o);
            }
        };
        return $.ajax(s);
    }

    // private function for handling file uploads (hat tip to YAHOO!)
    function fileUploadIframe(a) {
        var form = $form[0], el, i, s, g, id, $io, io, xhr, sub, n, timedOut, timeoutHandle;
        var deferred = $.Deferred();

        // #341
        deferred.abort = function(status) {
            xhr.abort(status);
        };

        if (a) {
            // ensure that every serialized input is still enabled
            for (i=0; i < elements.length; i++) {
                el = $(elements[i]);
                if ( hasProp ) {
                    el.prop('disabled', false);
                }
                else {
                    el.removeAttr('disabled');
                }
            }
        }

        s = $.extend(true, {}, $.ajaxSettings, options);
        s.context = s.context || s;
        id = 'jqFormIO' + (new Date().getTime());
        if (s.iframeTarget) {
            $io = $(s.iframeTarget);
            n = $io.attr2('name');
            if (!n) {
                $io.attr2('name', id);
            }
            else {
                id = n;
            }
        }
        else {
            $io = $('<iframe name="' + id + '" src="'+ s.iframeSrc +'" />');
            $io.css({ position: 'absolute', top: '-1000px', left: '-1000px' });
        }
        io = $io[0];


        xhr = { // mock object
            aborted: 0,
            responseText: null,
            responseXML: null,
            status: 0,
            statusText: 'n/a',
            getAllResponseHeaders: function() {},
            getResponseHeader: function() {},
            setRequestHeader: function() {},
            abort: function(status) {
                var e = (status === 'timeout' ? 'timeout' : 'aborted');
                log('aborting upload... ' + e);
                this.aborted = 1;

                try { // #214, #257
                    if (io.contentWindow.document.execCommand) {
                        io.contentWindow.document.execCommand('Stop');
                    }
                }
                catch(ignore) {}

                $io.attr('src', s.iframeSrc); // abort op in progress
                xhr.error = e;
                if (s.error) {
                    s.error.call(s.context, xhr, e, status);
                }
                if (g) {
                    $.event.trigger("ajaxError", [xhr, s, e]);
                }
                if (s.complete) {
                    s.complete.call(s.context, xhr, e);
                }
            }
        };

        g = s.global;
        // trigger ajax global events so that activity/block indicators work like normal
        if (g && 0 === $.active++) {
            $.event.trigger("ajaxStart");
        }
        if (g) {
            $.event.trigger("ajaxSend", [xhr, s]);
        }

        if (s.beforeSend && s.beforeSend.call(s.context, xhr, s) === false) {
            if (s.global) {
                $.active--;
            }
            deferred.reject();
            return deferred;
        }
        if (xhr.aborted) {
            deferred.reject();
            return deferred;
        }

        // add submitting element to data if we know it
        sub = form.clk;
        if (sub) {
            n = sub.name;
            if (n && !sub.disabled) {
                s.extraData = s.extraData || {};
                s.extraData[n] = sub.value;
                if (sub.type == "image") {
                    s.extraData[n+'.x'] = form.clk_x;
                    s.extraData[n+'.y'] = form.clk_y;
                }
            }
        }

        var CLIENT_TIMEOUT_ABORT = 1;
        var SERVER_ABORT = 2;
                
        function getDoc(frame) {
            /* it looks like contentWindow or contentDocument do not
             * carry the protocol property in ie8, when running under ssl
             * frame.document is the only valid response document, since
             * the protocol is know but not on the other two objects. strange?
             * "Same origin policy" http://en.wikipedia.org/wiki/Same_origin_policy
             */
            
            var doc = null;
            
            // IE8 cascading access check
            try {
                if (frame.contentWindow) {
                    doc = frame.contentWindow.document;
                }
            } catch(err) {
                // IE8 access denied under ssl & missing protocol
                log('cannot get iframe.contentWindow document: ' + err);
            }

            if (doc) { // successful getting content
                return doc;
            }

            try { // simply checking may throw in ie8 under ssl or mismatched protocol
                doc = frame.contentDocument ? frame.contentDocument : frame.document;
            } catch(err) {
                // last attempt
                log('cannot get iframe.contentDocument: ' + err);
                doc = frame.document;
            }
            return doc;
        }

        // Rails CSRF hack (thanks to Yvan Barthelemy)
        var csrf_token = $('meta[name=csrf-token]').attr('content');
        var csrf_param = $('meta[name=csrf-param]').attr('content');
        if (csrf_param && csrf_token) {
            s.extraData = s.extraData || {};
            s.extraData[csrf_param] = csrf_token;
        }

        // take a breath so that pending repaints get some cpu time before the upload starts
        function doSubmit() {
            // make sure form attrs are set
            var t = $form.attr2('target'), 
                a = $form.attr2('action'), 
                mp = 'multipart/form-data',
                et = $form.attr('enctype') || $form.attr('encoding') || mp;

            // update form attrs in IE friendly way
            form.setAttribute('target',id);
            if (!method || /post/i.test(method) ) {
                form.setAttribute('method', 'POST');
            }
            if (a != s.url) {
                form.setAttribute('action', s.url);
            }

            // ie borks in some cases when setting encoding
            if (! s.skipEncodingOverride && (!method || /post/i.test(method))) {
                $form.attr({
                    encoding: 'multipart/form-data',
                    enctype:  'multipart/form-data'
                });
            }

            // support timout
            if (s.timeout) {
                timeoutHandle = setTimeout(function() { timedOut = true; cb(CLIENT_TIMEOUT_ABORT); }, s.timeout);
            }

            // look for server aborts
            function checkState() {
                try {
                    var state = getDoc(io).readyState;
                    log('state = ' + state);
                    if (state && state.toLowerCase() == 'uninitialized') {
                        setTimeout(checkState,50);
                    }
                }
                catch(e) {
                    log('Server abort: ' , e, ' (', e.name, ')');
                    cb(SERVER_ABORT);
                    if (timeoutHandle) {
                        clearTimeout(timeoutHandle);
                    }
                    timeoutHandle = undefined;
                }
            }

            // add "extra" data to form if provided in options
            var extraInputs = [];
            try {
                if (s.extraData) {
                    for (var n in s.extraData) {
                        if (s.extraData.hasOwnProperty(n)) {
                           // if using the $.param format that allows for multiple values with the same name
                           if($.isPlainObject(s.extraData[n]) && s.extraData[n].hasOwnProperty('name') && s.extraData[n].hasOwnProperty('value')) {
                               extraInputs.push(
                               $('<input type="hidden" name="'+s.extraData[n].name+'">').val(s.extraData[n].value)
                                   .appendTo(form)[0]);
                           } else {
                               extraInputs.push(
                               $('<input type="hidden" name="'+n+'">').val(s.extraData[n])
                                   .appendTo(form)[0]);
                           }
                        }
                    }
                }

                if (!s.iframeTarget) {
                    // add iframe to doc and submit the form
                    $io.appendTo('body');
                }
                if (io.attachEvent) {
                    io.attachEvent('onload', cb);
                }
                else {
                    io.addEventListener('load', cb, false);
                }
                setTimeout(checkState,15);

                try {
                    form.submit();
                } catch(err) {
                    // just in case form has element with name/id of 'submit'
                    var submitFn = document.createElement('form').submit;
                    submitFn.apply(form);
                }
            }
            finally {
                // reset attrs and remove "extra" input elements
                form.setAttribute('action',a);
                form.setAttribute('enctype', et); // #380
                if(t) {
                    form.setAttribute('target', t);
                } else {
                    $form.removeAttr('target');
                }
                $(extraInputs).remove();
            }
        }

        if (s.forceSync) {
            doSubmit();
        }
        else {
            setTimeout(doSubmit, 10); // this lets dom updates render
        }

        var data, doc, domCheckCount = 50, callbackProcessed;

        function cb(e) {
            if (xhr.aborted || callbackProcessed) {
                return;
            }
            
            doc = getDoc(io);
            if(!doc) {
                log('cannot access response document');
                e = SERVER_ABORT;
            }
            if (e === CLIENT_TIMEOUT_ABORT && xhr) {
                xhr.abort('timeout');
                deferred.reject(xhr, 'timeout');
                return;
            }
            else if (e == SERVER_ABORT && xhr) {
                xhr.abort('server abort');
                deferred.reject(xhr, 'error', 'server abort');
                return;
            }

            if (!doc || doc.location.href == s.iframeSrc) {
                // response not received yet
                if (!timedOut) {
                    return;
                }
            }
            if (io.detachEvent) {
                io.detachEvent('onload', cb);
            }
            else {
                io.removeEventListener('load', cb, false);
            }

            var status = 'success', errMsg;
            try {
                if (timedOut) {
                    throw 'timeout';
                }

                var isXml = s.dataType == 'xml' || doc.XMLDocument || $.isXMLDoc(doc);
                log('isXml='+isXml);
                if (!isXml && window.opera && (doc.body === null || !doc.body.innerHTML)) {
                    if (--domCheckCount) {
                        // in some browsers (Opera) the iframe DOM is not always traversable when
                        // the onload callback fires, so we loop a bit to accommodate
                        log('requeing onLoad callback, DOM not available');
                        setTimeout(cb, 250);
                        return;
                    }
                    // let this fall through because server response could be an empty document
                    //log('Could not access iframe DOM after mutiple tries.');
                    //throw 'DOMException: not available';
                }

                //log('response detected');
                var docRoot = doc.body ? doc.body : doc.documentElement;
                xhr.responseText = docRoot ? docRoot.innerHTML : null;
                xhr.responseXML = doc.XMLDocument ? doc.XMLDocument : doc;
                if (isXml) {
                    s.dataType = 'xml';
                }
                xhr.getResponseHeader = function(header){
                    var headers = {'content-type': s.dataType};
                    return headers[header.toLowerCase()];
                };
                // support for XHR 'status' & 'statusText' emulation :
                if (docRoot) {
                    xhr.status = Number( docRoot.getAttribute('status') ) || xhr.status;
                    xhr.statusText = docRoot.getAttribute('statusText') || xhr.statusText;
                }

                var dt = (s.dataType || '').toLowerCase();
                var scr = /(json|script|text)/.test(dt);
                if (scr || s.textarea) {
                    // see if user embedded response in textarea
                    var ta = doc.getElementsByTagName('textarea')[0];
                    if (ta) {
                        xhr.responseText = ta.value;
                        // support for XHR 'status' & 'statusText' emulation :
                        xhr.status = Number( ta.getAttribute('status') ) || xhr.status;
                        xhr.statusText = ta.getAttribute('statusText') || xhr.statusText;
                    }
                    else if (scr) {
                        // account for browsers injecting pre around json response
                        var pre = doc.getElementsByTagName('pre')[0];
                        var b = doc.getElementsByTagName('body')[0];
                        if (pre) {
                            xhr.responseText = pre.textContent ? pre.textContent : pre.innerText;
                        }
                        else if (b) {
                            xhr.responseText = b.textContent ? b.textContent : b.innerText;
                        }
                    }
                }
                else if (dt == 'xml' && !xhr.responseXML && xhr.responseText) {
                    xhr.responseXML = toXml(xhr.responseText);
                }

                try {
                    data = httpData(xhr, dt, s);
                }
                catch (err) {
                    status = 'parsererror';
                    xhr.error = errMsg = (err || status);
                }
            }
            catch (err) {
                log('error caught: ',err);
                status = 'error';
                xhr.error = errMsg = (err || status);
            }

            if (xhr.aborted) {
                log('upload aborted');
                status = null;
            }

            if (xhr.status) { // we've set xhr.status
                status = (xhr.status >= 200 && xhr.status < 300 || xhr.status === 304) ? 'success' : 'error';
            }

            // ordering of these callbacks/triggers is odd, but that's how $.ajax does it
            if (status === 'success') {
                if (s.success) {
                    s.success.call(s.context, data, 'success', xhr);
                }
                deferred.resolve(xhr.responseText, 'success', xhr);
                if (g) {
                    $.event.trigger("ajaxSuccess", [xhr, s]);
                }
            }
            else if (status) {
                if (errMsg === undefined) {
                    errMsg = xhr.statusText;
                }
                if (s.error) {
                    s.error.call(s.context, xhr, status, errMsg);
                }
                deferred.reject(xhr, 'error', errMsg);
                if (g) {
                    $.event.trigger("ajaxError", [xhr, s, errMsg]);
                }
            }

            if (g) {
                $.event.trigger("ajaxComplete", [xhr, s]);
            }

            if (g && ! --$.active) {
                $.event.trigger("ajaxStop");
            }

            if (s.complete) {
                s.complete.call(s.context, xhr, status);
            }

            callbackProcessed = true;
            if (s.timeout) {
                clearTimeout(timeoutHandle);
            }

            // clean up
            setTimeout(function() {
                if (!s.iframeTarget) {
                    $io.remove();
                }
                else { //adding else to clean up existing iframe response.
                    $io.attr('src', s.iframeSrc);
                }
                xhr.responseXML = null;
            }, 100);
        }

        var toXml = $.parseXML || function(s, doc) { // use parseXML if available (jQuery 1.5+)
            if (window.ActiveXObject) {
                doc = new ActiveXObject('Microsoft.XMLDOM');
                doc.async = 'false';
                doc.loadXML(s);
            }
            else {
                doc = (new DOMParser()).parseFromString(s, 'text/xml');
            }
            return (doc && doc.documentElement && doc.documentElement.nodeName != 'parsererror') ? doc : null;
        };
        var parseJSON = $.parseJSON || function(s) {
            /*jslint evil:true */
            return window['eval']('(' + s + ')');
        };

        var httpData = function( xhr, type, s ) { // mostly lifted from jq1.4.4

            var ct = xhr.getResponseHeader('content-type') || '',
                xml = type === 'xml' || !type && ct.indexOf('xml') >= 0,
                data = xml ? xhr.responseXML : xhr.responseText;

            if (xml && data.documentElement.nodeName === 'parsererror') {
                if ($.error) {
                    $.error('parsererror');
                }
            }
            if (s && s.dataFilter) {
                data = s.dataFilter(data, type);
            }
            if (typeof data === 'string') {
                if (type === 'json' || !type && ct.indexOf('json') >= 0) {
                    data = parseJSON(data);
                } else if (type === "script" || !type && ct.indexOf("javascript") >= 0) {
                    $.globalEval(data);
                }
            }
            return data;
        };

        return deferred;
    }
};

/**
 * ajaxForm() provides a mechanism for fully automating form submission.
 *
 * The advantages of using this method instead of ajaxSubmit() are:
 *
 * 1: This method will include coordinates for <input type="image" /> elements (if the element
 *    is used to submit the form).
 * 2. This method will include the submit element's name/value data (for the element that was
 *    used to submit the form).
 * 3. This method binds the submit() method to the form for you.
 *
 * The options argument for ajaxForm works exactly as it does for ajaxSubmit.  ajaxForm merely
 * passes the options argument along after properly binding events for submit elements and
 * the form itself.
 */
$.fn.ajaxForm = function(options) {
    options = options || {};
    options.delegation = options.delegation && $.isFunction($.fn.on);

    // in jQuery 1.3+ we can fix mistakes with the ready state
    if (!options.delegation && this.length === 0) {
        var o = { s: this.selector, c: this.context };
        if (!$.isReady && o.s) {
            log('DOM not ready, queuing ajaxForm');
            $(function() {
                $(o.s,o.c).ajaxForm(options);
            });
            return this;
        }
        // is your DOM ready?  http://docs.jquery.com/Tutorials:Introducing_$(document).ready()
        log('terminating; zero elements found by selector' + ($.isReady ? '' : ' (DOM not ready)'));
        return this;
    }

    if ( options.delegation ) {
        $(document)
            .off('submit.form-plugin', this.selector, doAjaxSubmit)
            .off('click.form-plugin', this.selector, captureSubmittingElement)
            .on('submit.form-plugin', this.selector, options, doAjaxSubmit)
            .on('click.form-plugin', this.selector, options, captureSubmittingElement);
        return this;
    }

    return this.ajaxFormUnbind()
        .bind('submit.form-plugin', options, doAjaxSubmit)
        .bind('click.form-plugin', options, captureSubmittingElement);
};

// private event handlers
function doAjaxSubmit(e) {
    /*jshint validthis:true */
    var options = e.data;
    if (!e.isDefaultPrevented()) { // if event has been canceled, don't proceed
        e.preventDefault();
        $(e.target).ajaxSubmit(options); // #365
    }
}

function captureSubmittingElement(e) {
    /*jshint validthis:true */
    var target = e.target;
    var $el = $(target);
    if (!($el.is("[type=submit],[type=image]"))) {
        // is this a child element of the submit el?  (ex: a span within a button)
        var t = $el.closest('[type=submit]');
        if (t.length === 0) {
            return;
        }
        target = t[0];
    }
    var form = this;
    form.clk = target;
    if (target.type == 'image') {
        if (e.offsetX !== undefined) {
            form.clk_x = e.offsetX;
            form.clk_y = e.offsetY;
        } else if (typeof $.fn.offset == 'function') {
            var offset = $el.offset();
            form.clk_x = e.pageX - offset.left;
            form.clk_y = e.pageY - offset.top;
        } else {
            form.clk_x = e.pageX - target.offsetLeft;
            form.clk_y = e.pageY - target.offsetTop;
        }
    }
    // clear form vars
    setTimeout(function() { form.clk = form.clk_x = form.clk_y = null; }, 100);
}


// ajaxFormUnbind unbinds the event handlers that were bound by ajaxForm
$.fn.ajaxFormUnbind = function() {
    return this.unbind('submit.form-plugin click.form-plugin');
};

/**
 * formToArray() gathers form element data into an array of objects that can
 * be passed to any of the following ajax functions: $.get, $.post, or load.
 * Each object in the array has both a 'name' and 'value' property.  An example of
 * an array for a simple login form might be:
 *
 * [ { name: 'username', value: 'jresig' }, { name: 'password', value: 'secret' } ]
 *
 * It is this array that is passed to pre-submit callback functions provided to the
 * ajaxSubmit() and ajaxForm() methods.
 */
$.fn.formToArray = function(semantic, elements) {
    var a = [];
    if (this.length === 0) {
        return a;
    }

    var form = this[0];
    var formId = this.attr('id');
    var els = semantic ? form.getElementsByTagName('*') : form.elements;
    var els2;

    if (els && !/MSIE [678]/.test(navigator.userAgent)) { // #390
        els = $(els).get();  // convert to standard array
    }

    // #386; account for inputs outside the form which use the 'form' attribute
    if ( formId ) {
        els2 = $(':input[form="' + formId + '"]').get(); // hat tip @thet
        if ( els2.length ) {
            els = (els || []).concat(els2);
        }
    }

    if (!els || !els.length) {
        return a;
    }

    var i,j,n,v,el,max,jmax;
    for(i=0, max=els.length; i < max; i++) {
        el = els[i];
        n = el.name;
        if (!n || el.disabled) {
            continue;
        }

        if (semantic && form.clk && el.type == "image") {
            // handle image inputs on the fly when semantic == true
            if(form.clk == el) {
                a.push({name: n, value: $(el).val(), type: el.type });
                a.push({name: n+'.x', value: form.clk_x}, {name: n+'.y', value: form.clk_y});
            }
            continue;
        }

        v = $.fieldValue(el, true);
        if (v && v.constructor == Array) {
            if (elements) {
                elements.push(el);
            }
            for(j=0, jmax=v.length; j < jmax; j++) {
                a.push({name: n, value: v[j]});
            }
        }
        else if (feature.fileapi && el.type == 'file') {
            if (elements) {
                elements.push(el);
            }
            var files = el.files;
            if (files.length) {
                for (j=0; j < files.length; j++) {
                    a.push({name: n, value: files[j], type: el.type});
                }
            }
            else {
                // #180
                a.push({ name: n, value: '', type: el.type });
            }
        }
        else if (v !== null && typeof v != 'undefined') {
            if (elements) {
                elements.push(el);
            }
            a.push({name: n, value: v, type: el.type, required: el.required});
        }
    }

    if (!semantic && form.clk) {
        // input type=='image' are not found in elements array! handle it here
        var $input = $(form.clk), input = $input[0];
        n = input.name;
        if (n && !input.disabled && input.type == 'image') {
            a.push({name: n, value: $input.val()});
            a.push({name: n+'.x', value: form.clk_x}, {name: n+'.y', value: form.clk_y});
        }
    }
    return a;
};

/**
 * Serializes form data into a 'submittable' string. This method will return a string
 * in the format: name1=value1&amp;name2=value2
 */
$.fn.formSerialize = function(semantic) {
    //hand off to jQuery.param for proper encoding
    return $.param(this.formToArray(semantic));
};

/**
 * Serializes all field elements in the jQuery object into a query string.
 * This method will return a string in the format: name1=value1&amp;name2=value2
 */
$.fn.fieldSerialize = function(successful) {
    var a = [];
    this.each(function() {
        var n = this.name;
        if (!n) {
            return;
        }
        var v = $.fieldValue(this, successful);
        if (v && v.constructor == Array) {
            for (var i=0,max=v.length; i < max; i++) {
                a.push({name: n, value: v[i]});
            }
        }
        else if (v !== null && typeof v != 'undefined') {
            a.push({name: this.name, value: v});
        }
    });
    //hand off to jQuery.param for proper encoding
    return $.param(a);
};

/**
 * Returns the value(s) of the element in the matched set.  For example, consider the following form:
 *
 *  <form><fieldset>
 *      <input name="A" type="text" />
 *      <input name="A" type="text" />
 *      <input name="B" type="checkbox" value="B1" />
 *      <input name="B" type="checkbox" value="B2"/>
 *      <input name="C" type="radio" value="C1" />
 *      <input name="C" type="radio" value="C2" />
 *  </fieldset></form>
 *
 *  var v = $('input[type=text]').fieldValue();
 *  // if no values are entered into the text inputs
 *  v == ['','']
 *  // if values entered into the text inputs are 'foo' and 'bar'
 *  v == ['foo','bar']
 *
 *  var v = $('input[type=checkbox]').fieldValue();
 *  // if neither checkbox is checked
 *  v === undefined
 *  // if both checkboxes are checked
 *  v == ['B1', 'B2']
 *
 *  var v = $('input[type=radio]').fieldValue();
 *  // if neither radio is checked
 *  v === undefined
 *  // if first radio is checked
 *  v == ['C1']
 *
 * The successful argument controls whether or not the field element must be 'successful'
 * (per http://www.w3.org/TR/html4/interact/forms.html#successful-controls).
 * The default value of the successful argument is true.  If this value is false the value(s)
 * for each element is returned.
 *
 * Note: This method *always* returns an array.  If no valid value can be determined the
 *    array will be empty, otherwise it will contain one or more values.
 */
$.fn.fieldValue = function(successful) {
    for (var val=[], i=0, max=this.length; i < max; i++) {
        var el = this[i];
        var v = $.fieldValue(el, successful);
        if (v === null || typeof v == 'undefined' || (v.constructor == Array && !v.length)) {
            continue;
        }
        if (v.constructor == Array) {
            $.merge(val, v);
        }
        else {
            val.push(v);
        }
    }
    return val;
};

/**
 * Returns the value of the field element.
 */
$.fieldValue = function(el, successful) {
    var n = el.name, t = el.type, tag = el.tagName.toLowerCase();
    if (successful === undefined) {
        successful = true;
    }

    if (successful && (!n || el.disabled || t == 'reset' || t == 'button' ||
        (t == 'checkbox' || t == 'radio') && !el.checked ||
        (t == 'submit' || t == 'image') && el.form && el.form.clk != el ||
        tag == 'select' && el.selectedIndex == -1)) {
            return null;
    }

    if (tag == 'select') {
        var index = el.selectedIndex;
        if (index < 0) {
            return null;
        }
        var a = [], ops = el.options;
        var one = (t == 'select-one');
        var max = (one ? index+1 : ops.length);
        for(var i=(one ? index : 0); i < max; i++) {
            var op = ops[i];
            if (op.selected) {
                var v = op.value;
                if (!v) { // extra pain for IE...
                    v = (op.attributes && op.attributes.value && !(op.attributes.value.specified)) ? op.text : op.value;
                }
                if (one) {
                    return v;
                }
                a.push(v);
            }
        }
        return a;
    }
    return $(el).val();
};

/**
 * Clears the form data.  Takes the following actions on the form's input fields:
 *  - input text fields will have their 'value' property set to the empty string
 *  - select elements will have their 'selectedIndex' property set to -1
 *  - checkbox and radio inputs will have their 'checked' property set to false
 *  - inputs of type submit, button, reset, and hidden will *not* be effected
 *  - button elements will *not* be effected
 */
$.fn.clearForm = function(includeHidden) {
    return this.each(function() {
        $('input,select,textarea', this).clearFields(includeHidden);
    });
};

/**
 * Clears the selected form elements.
 */
$.fn.clearFields = $.fn.clearInputs = function(includeHidden) {
    var re = /^(?:color|date|datetime|email|month|number|password|range|search|tel|text|time|url|week)$/i; // 'hidden' is not in this list
    return this.each(function() {
        var t = this.type, tag = this.tagName.toLowerCase();
        if (re.test(t) || tag == 'textarea') {
            this.value = '';
        }
        else if (t == 'checkbox' || t == 'radio') {
            this.checked = false;
        }
        else if (tag == 'select') {
            this.selectedIndex = -1;
        }
        else if (t == "file") {
            if (/MSIE/.test(navigator.userAgent)) {
                $(this).replaceWith($(this).clone(true));
            } else {
                $(this).val('');
            }
        }
        else if (includeHidden) {
            // includeHidden can be the value true, or it can be a selector string
            // indicating a special test; for example:
            //  $('#myForm').clearForm('.special:hidden')
            // the above would clean hidden inputs that have the class of 'special'
            if ( (includeHidden === true && /hidden/.test(t)) ||
                 (typeof includeHidden == 'string' && $(this).is(includeHidden)) ) {
                this.value = '';
            }
        }
    });
};

/**
 * Resets the form data.  Causes all form elements to be reset to their original value.
 */
$.fn.resetForm = function() {
    return this.each(function() {
        // guard against an input with the name of 'reset'
        // note that IE reports the reset function as an 'object'
        if (typeof this.reset == 'function' || (typeof this.reset == 'object' && !this.reset.nodeType)) {
            this.reset();
        }
    });
};

/**
 * Enables or disables any matching elements.
 */
$.fn.enable = function(b) {
    if (b === undefined) {
        b = true;
    }
    return this.each(function() {
        this.disabled = !b;
    });
};

/**
 * Checks/unchecks any matching checkboxes or radio buttons and
 * selects/deselects and matching option elements.
 */
$.fn.selected = function(select) {
    if (select === undefined) {
        select = true;
    }
    return this.each(function() {
        var t = this.type;
        if (t == 'checkbox' || t == 'radio') {
            this.checked = select;
        }
        else if (this.tagName.toLowerCase() == 'option') {
            var $sel = $(this).parent('select');
            if (select && $sel[0] && $sel[0].type == 'select-one') {
                // deselect all other options
                $sel.find('option').selected(false);
            }
            this.selected = select;
        }
    });
};

// expose debug var
$.fn.ajaxSubmit.debug = false;

// helper fn for console logging
function log() {
    if (!$.fn.ajaxSubmit.debug) {
        return;
    }
    var msg = '[jquery.form] ' + Array.prototype.join.call(arguments,'');
    if (window.console && window.console.log) {
        window.console.log(msg);
    }
    else if (window.opera && window.opera.postError) {
        window.opera.postError(msg);
    }
}

}));

/* ========================================================================
 * Bootstrap: popover.js v3.3.6
 * http://getbootstrap.com/javascript/#popovers
 * ========================================================================
 * Copyright 2011-2015 Twitter, Inc.
 * Licensed under MIT (https://github.com/twbs/bootstrap/blob/master/LICENSE)
 * ======================================================================== */
 (function($) {

  //BlocksIt default options
  var blocksOptions = {
    numOfCol: 5,
    offsetX: 5,
    offsetY: 5,
    blockElement: 'div'
  };
  
  //dynamic variable
  var container, colwidth;
  var blockarr = [];
  
  //ie indexOf fix
  if (!Array.prototype.indexOf) {
    Array.prototype.indexOf = function(elt /*, from*/) {
      var len = this.length >>> 0;

      var from = Number(arguments[1]) || 0;
      from = (from < 0) ? Math.ceil(from) : Math.floor(from);
      if (from < 0)
        from += len;

        for (; from < len; from++) {
          if (from in this &&
          this[from] === elt)
          return from;
        }
      return -1;
    };
  }
  
  //create empty blockarr
  var createEmptyBlockarr = function() {
    //empty blockarr
    blockarr = [];
    for(var i=0; i<blocksOptions.numOfCol; i++) {
      blockarrPush('empty-'+i, i, 0, 1, -blocksOptions.offsetY);
    }
  }
  
  //add new block to blockarr
  var blockarrPush = function(id, x, y, width, height) {
    //define block object based on block width
    for(var i=0; i<width; i++) {
      var block = new Object();
      block.x = x + i;
      block.size = width;
      block.endY = y + height + blocksOptions.offsetY*2;
      
      blockarr.push(block);
    }
  }
  
  //remove block from blockarr
  var blockarrRemove = function(x, num) {
    for(var i=0; i<num; i++) {
      //remove block beside
      var index = getBlockIndex(x+i, 'x');
      blockarr.splice(index, 1);
    }
  }
  
  //retrieve block index based on block's x position
  var getBlockIndex = function(value, type) {
    
    for(var i=0; i<blockarr.length; i++) {
      var obj = blockarr[i];
      if(type == "x" && obj.x == value) {
        return i;
      } else if(type == "endY" && obj.endY == value) {
        return i;
      }
    }
  }

  //get height from blockarr range based on block.x and size
  //retrun min and max height
  var getHeightArr = function(x, size) {
    var temparr = [];
    for(var i=0; i<size; i++) {
      temparr.push(blockarr[getBlockIndex(x+i, 'x')].endY);
    } 
    var min = Math.min.apply(Math, temparr);
    var max = Math.max.apply(Math, temparr);
    
    return [min, max, temparr.indexOf(min)];
  }
  
  //get block x and y position
  var getBlockPostion = function(size) {
    
    //if block width is not default 1
    //extra algorithm check
    if(size > 1) {
      //prevent extra loop
      var arrlimit = blockarr.length - size;
      //define temp variable
      var defined = false;
      var tempHeight, tempIndex;
      
      for(var i=0; i<blockarr.length; i++) {
        var obj = blockarr[i];
        var x = obj.x;

        //check for block within range only
        if(x >= 0 && x <= arrlimit) {
          var heightarr = getHeightArr(x, size);
          
          //get shortest group blocks
          if(!defined) {
            defined = true;
            tempHeight = heightarr;
            tempIndex = x;
          } else {
            if(heightarr[1] < tempHeight[1]) {
              tempHeight = heightarr;
              tempIndex = x;
            }
          }
        }
      }
      return [tempIndex, tempHeight[1]];
    } else { //simple check for block with width 1
      tempHeight = getHeightArr(0, blockarr.length);
      return [tempHeight[2], tempHeight[0]];
    } 
  }
  
  //set block position
  var setPosition = function(obj, index) {
    //check block size
    if(!obj.data('size') || obj.data('size') < 0) {
      obj.data('size', 1);
    } else if(obj.data('size') > blocksOptions.numOfCol) {
      obj.data('size', blocksOptions.numOfCol);
    }
    
    //define block data
    var pos = getBlockPostion(obj.data('size'));
    var blockWidth = colwidth * obj.data('size') - (obj.outerWidth() - obj.width());

    //update style first before get object height
    obj.css({
      'width': blockWidth - blocksOptions.offsetX*2,
      'left': pos[0] * colwidth,
      'top': pos[1],
      'position': 'absolute'
    });
    
    var blockHeight = obj.outerHeight();
    
    //modify blockarr for new block
    blockarrRemove(pos[0], obj.data('size'));
    blockarrPush(obj.attr('id'), pos[0], pos[1], obj.data('size'), blockHeight);  
  }
  
  $.fn.BlocksIt = function(options) {
    //BlocksIt options
    if (options && typeof options === 'object') {
      $.extend(blocksOptions, options);
    }
    
    container = $(this);
    colwidth = container.width() / blocksOptions.numOfCol;

    //create empty blockarr
    createEmptyBlockarr();

    container.children(blocksOptions.blockElement).each(function(e) {
      setPosition($(this), e);
    });
    
    //set final height of container
    var heightarr = getHeightArr(0, blockarr.length);
    container.height(heightarr[1] + blocksOptions.offsetY);
    
    return this;
  }

 })(jQuery);
(function ($) {
   'use strict';

   // TOOLTIP PUBLIC CLASS DEFINITION
   // ===============================

   var Tooltip = function (element, options) {
     this.type       = null
     this.options    = null
     this.enabled    = null
     this.timeout    = null
     this.hoverState = null
     this.$element   = null
     this.inState    = null

     this.init('tooltip', element, options)
   }

   Tooltip.VERSION  = '3.3.6'

   Tooltip.TRANSITION_DURATION = 150

   Tooltip.DEFAULTS = {
     animation: true,
     placement: 'top',
     selector: false,
     template: '<div class="tooltip" role="tooltip"><div class="tooltip-arrow"></div><div class="tooltip-inner"></div></div>',
     trigger: 'hover focus',
     title: '',
     delay: 0,
     html: false,
     container: false,
     viewport: {
       selector: 'body',
       padding: 0
     }
   }

   Tooltip.prototype.init = function (type, element, options) {
     this.enabled   = true
     this.type      = type
     this.$element  = $(element)
     this.options   = this.getOptions(options)
     this.$viewport = this.options.viewport && $($.isFunction(this.options.viewport) ? this.options.viewport.call(this, this.$element) : (this.options.viewport.selector || this.options.viewport))
     this.inState   = { click: false, hover: false, focus: false }

     if (this.$element[0] instanceof document.constructor && !this.options.selector) {
       throw new Error('`selector` option must be specified when initializing ' + this.type + ' on the window.document object!')
     }

     var triggers = this.options.trigger.split(' ')

     for (var i = triggers.length; i--;) {
       var trigger = triggers[i]

       if (trigger == 'click') {
         this.$element.on('click.' + this.type, this.options.selector, $.proxy(this.toggle, this))
       } else if (trigger != 'manual') {
         var eventIn  = trigger == 'hover' ? 'mouseenter' : 'focusin'
         var eventOut = trigger == 'hover' ? 'mouseleave' : 'focusout'

         this.$element.on(eventIn  + '.' + this.type, this.options.selector, $.proxy(this.enter, this))
         this.$element.on(eventOut + '.' + this.type, this.options.selector, $.proxy(this.leave, this))
       }
     }

     this.options.selector ?
       (this._options = $.extend({}, this.options, { trigger: 'manual', selector: '' })) :
       this.fixTitle()
   }

   Tooltip.prototype.getDefaults = function () {
     return Tooltip.DEFAULTS
   }

   Tooltip.prototype.getOptions = function (options) {
     options = $.extend({}, this.getDefaults(), this.$element.data(), options)

     if (options.delay && typeof options.delay == 'number') {
       options.delay = {
         show: options.delay,
         hide: options.delay
       }
     }

     return options
   }

   Tooltip.prototype.getDelegateOptions = function () {
     var options  = {}
     var defaults = this.getDefaults()

     this._options && $.each(this._options, function (key, value) {
       if (defaults[key] != value) options[key] = value
     })

     return options
   }

   Tooltip.prototype.enter = function (obj) {
     var self = obj instanceof this.constructor ?
       obj : $(obj.currentTarget).data('bs.' + this.type)

     if (!self) {
       self = new this.constructor(obj.currentTarget, this.getDelegateOptions())
       $(obj.currentTarget).data('bs.' + this.type, self)
     }

     if (obj instanceof $.Event) {
       self.inState[obj.type == 'focusin' ? 'focus' : 'hover'] = true
     }

     if (self.tip().hasClass('in') || self.hoverState == 'in') {
       self.hoverState = 'in'
       return
     }

     clearTimeout(self.timeout)

     self.hoverState = 'in'

     if (!self.options.delay || !self.options.delay.show) return self.show()

     self.timeout = setTimeout(function () {
       if (self.hoverState == 'in') self.show()
     }, self.options.delay.show)
   }

   Tooltip.prototype.isInStateTrue = function () {
     for (var key in this.inState) {
       if (this.inState[key]) return true
     }

     return false
   }

   Tooltip.prototype.leave = function (obj) {
     var self = obj instanceof this.constructor ?
       obj : $(obj.currentTarget).data('bs.' + this.type)

     if (!self) {
       self = new this.constructor(obj.currentTarget, this.getDelegateOptions())
       $(obj.currentTarget).data('bs.' + this.type, self)
     }

     if (obj instanceof $.Event) {
       self.inState[obj.type == 'focusout' ? 'focus' : 'hover'] = false
     }

     if (self.isInStateTrue()) return

     clearTimeout(self.timeout)

     self.hoverState = 'out'

     if (!self.options.delay || !self.options.delay.hide) return self.hide()

     self.timeout = setTimeout(function () {
       if (self.hoverState == 'out') self.hide()
     }, self.options.delay.hide)
   }

   Tooltip.prototype.show = function () {
     var e = $.Event('show.bs.' + this.type)

     if (this.hasContent() && this.enabled) {
       this.$element.trigger(e)

       var inDom = $.contains(this.$element[0].ownerDocument.documentElement, this.$element[0])
       if (e.isDefaultPrevented() || !inDom) return
       var that = this

       var $tip = this.tip()

       var tipId = this.getUID(this.type)

       this.setContent()
       $tip.attr('id', tipId)
       this.$element.attr('aria-describedby', tipId)

       if (this.options.animation) $tip.addClass('fade')

       var placement = typeof this.options.placement == 'function' ?
         this.options.placement.call(this, $tip[0], this.$element[0]) :
         this.options.placement

       var autoToken = /\s?auto?\s?/i
       var autoPlace = autoToken.test(placement)
       if (autoPlace) placement = placement.replace(autoToken, '') || 'top'

       $tip
         .detach()
         .css({ top: 0, left: 0, display: 'block' })
         .addClass(placement)
         .data('bs.' + this.type, this)

       this.options.container ? $tip.appendTo(this.options.container) : $tip.insertAfter(this.$element)
       this.$element.trigger('inserted.bs.' + this.type)

       var pos          = this.getPosition()
       var actualWidth  = $tip[0].offsetWidth
       var actualHeight = $tip[0].offsetHeight

       if (autoPlace) {
         var orgPlacement = placement
         var viewportDim = this.getPosition(this.$viewport)

         placement = placement == 'bottom' && pos.bottom + actualHeight > viewportDim.bottom ? 'top'    :
                     placement == 'top'    && pos.top    - actualHeight < viewportDim.top    ? 'bottom' :
                     placement == 'right'  && pos.right  + actualWidth  > viewportDim.width  ? 'left'   :
                     placement == 'left'   && pos.left   - actualWidth  < viewportDim.left   ? 'right'  :
                     placement

         $tip
           .removeClass(orgPlacement)
           .addClass(placement)
       }

       var calculatedOffset = this.getCalculatedOffset(placement, pos, actualWidth, actualHeight)

       this.applyPlacement(calculatedOffset, placement)

       var complete = function () {
         var prevHoverState = that.hoverState
         that.$element.trigger('shown.bs.' + that.type)
         that.hoverState = null

         if (prevHoverState == 'out') that.leave(that)
       }

       $.support.transition && this.$tip.hasClass('fade') ?
         $tip
           .one('bsTransitionEnd', complete)
           .emulateTransitionEnd(Tooltip.TRANSITION_DURATION) :
         complete()
     }
   }

   Tooltip.prototype.applyPlacement = function (offset, placement) {
     var $tip   = this.tip()
     var width  = $tip[0].offsetWidth
     var height = $tip[0].offsetHeight

     // manually read margins because getBoundingClientRect includes difference
     var marginTop = parseInt($tip.css('margin-top'), 10)
     var marginLeft = parseInt($tip.css('margin-left'), 10)

     // we must check for NaN for ie 8/9
     if (isNaN(marginTop))  marginTop  = 0
     if (isNaN(marginLeft)) marginLeft = 0

     offset.top  += marginTop
     offset.left += marginLeft

     // $.fn.offset doesn't round pixel values
     // so we use setOffset directly with our own function B-0
     $.offset.setOffset($tip[0], $.extend({
       using: function (props) {
         $tip.css({
           top: Math.round(props.top),
           left: Math.round(props.left)
         })
       }
     }, offset), 0)

     $tip.addClass('in')

     // check to see if placing tip in new offset caused the tip to resize itself
     var actualWidth  = $tip[0].offsetWidth
     var actualHeight = $tip[0].offsetHeight

     if (placement == 'top' && actualHeight != height) {
       offset.top = offset.top + height - actualHeight
     }

     var delta = this.getViewportAdjustedDelta(placement, offset, actualWidth, actualHeight)

     if (delta.left) offset.left += delta.left
     else offset.top += delta.top

     var isVertical          = /top|bottom/.test(placement)
     var arrowDelta          = isVertical ? delta.left * 2 - width + actualWidth : delta.top * 2 - height + actualHeight
     var arrowOffsetPosition = isVertical ? 'offsetWidth' : 'offsetHeight'

     $tip.offset(offset)
     this.replaceArrow(arrowDelta, $tip[0][arrowOffsetPosition], isVertical)
   }

   Tooltip.prototype.replaceArrow = function (delta, dimension, isVertical) {
     this.arrow()
       .css(isVertical ? 'left' : 'top', 50 * (1 - delta / dimension) + '%')
       .css(isVertical ? 'top' : 'left', '')
   }

   Tooltip.prototype.setContent = function () {
     var $tip  = this.tip()
     var title = this.getTitle()

     $tip.find('.tooltip-inner')[this.options.html ? 'html' : 'text'](title)
     $tip.removeClass('fade in top bottom left right')
   }

   Tooltip.prototype.hide = function (callback) {
     var that = this
     var $tip = $(this.$tip)
     var e    = $.Event('hide.bs.' + this.type)

     function complete() {
       if (that.hoverState != 'in') $tip.detach()
       that.$element
         .removeAttr('aria-describedby')
         .trigger('hidden.bs.' + that.type)
       callback && callback()
     }

     this.$element.trigger(e)

     if (e.isDefaultPrevented()) return

     $tip.removeClass('in')

     $.support.transition && $tip.hasClass('fade') ?
       $tip
         .one('bsTransitionEnd', complete)
         .emulateTransitionEnd(Tooltip.TRANSITION_DURATION) :
       complete()

     this.hoverState = null

     return this
   }

   Tooltip.prototype.fixTitle = function () {
     var $e = this.$element
     if ($e.attr('title') || typeof $e.attr('data-original-title') != 'string') {
       $e.attr('data-original-title', $e.attr('title') || '').attr('title', '')
     }
   }

   Tooltip.prototype.hasContent = function () {
     return this.getTitle()
   }

   Tooltip.prototype.getPosition = function ($element) {
     $element   = $element || this.$element

     var el     = $element[0]
     var isBody = el.tagName == 'BODY'

     var elRect    = el.getBoundingClientRect()
     if (elRect.width == null) {
       // width and height are missing in IE8, so compute them manually; see https://github.com/twbs/bootstrap/issues/14093
       elRect = $.extend({}, elRect, { width: elRect.right - elRect.left, height: elRect.bottom - elRect.top })
     }
     var elOffset  = isBody ? { top: 0, left: 0 } : $element.offset()
     var scroll    = { scroll: isBody ? document.documentElement.scrollTop || document.body.scrollTop : $element.scrollTop() }
     var outerDims = isBody ? { width: $(window).width(), height: $(window).height() } : null

     return $.extend({}, elRect, scroll, outerDims, elOffset)
   }

   Tooltip.prototype.getCalculatedOffset = function (placement, pos, actualWidth, actualHeight) {
     return placement == 'bottom' ? { top: pos.top + pos.height,   left: pos.left + pos.width / 2 - actualWidth / 2 } :
            placement == 'top'    ? { top: pos.top - actualHeight, left: pos.left + pos.width / 2 - actualWidth / 2 } :
            placement == 'left'   ? { top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left - actualWidth } :
         /* placement == 'right' */ { top: pos.top + pos.height / 2 - actualHeight / 2, left: pos.left + pos.width }

   }

   Tooltip.prototype.getViewportAdjustedDelta = function (placement, pos, actualWidth, actualHeight) {
     var delta = { top: 0, left: 0 }
     if (!this.$viewport) return delta

     var viewportPadding = this.options.viewport && this.options.viewport.padding || 0
     var viewportDimensions = this.getPosition(this.$viewport)

     if (/right|left/.test(placement)) {
       var topEdgeOffset    = pos.top - viewportPadding - viewportDimensions.scroll
       var bottomEdgeOffset = pos.top + viewportPadding - viewportDimensions.scroll + actualHeight
       if (topEdgeOffset < viewportDimensions.top) { // top overflow
         delta.top = viewportDimensions.top - topEdgeOffset
       } else if (bottomEdgeOffset > viewportDimensions.top + viewportDimensions.height) { // bottom overflow
         delta.top = viewportDimensions.top + viewportDimensions.height - bottomEdgeOffset
       }
     } else {
       var leftEdgeOffset  = pos.left - viewportPadding
       var rightEdgeOffset = pos.left + viewportPadding + actualWidth
       if (leftEdgeOffset < viewportDimensions.left) { // left overflow
         delta.left = viewportDimensions.left - leftEdgeOffset
       } else if (rightEdgeOffset > viewportDimensions.right) { // right overflow
         delta.left = viewportDimensions.left + viewportDimensions.width - rightEdgeOffset
       }
     }

     return delta
   }

   Tooltip.prototype.getTitle = function () {
     var title
     var $e = this.$element
     var o  = this.options

     title = $e.attr('data-original-title')
       || (typeof o.title == 'function' ? o.title.call($e[0]) :  o.title)

     return title
   }

   Tooltip.prototype.getUID = function (prefix) {
     do prefix += ~~(Math.random() * 1000000)
     while (document.getElementById(prefix))
     return prefix
   }

   Tooltip.prototype.tip = function () {
     if (!this.$tip) {
       this.$tip = $(this.options.template)
       if (this.$tip.length != 1) {
         throw new Error(this.type + ' `template` option must consist of exactly 1 top-level element!')
       }
     }
     return this.$tip
   }

   Tooltip.prototype.arrow = function () {
     return (this.$arrow = this.$arrow || this.tip().find('.tooltip-arrow'))
   }

   Tooltip.prototype.enable = function () {
     this.enabled = true
   }

   Tooltip.prototype.disable = function () {
     this.enabled = false
   }

   Tooltip.prototype.toggleEnabled = function () {
     this.enabled = !this.enabled
   }

   Tooltip.prototype.toggle = function (e) {
     var self = this
     if (e) {
       self = $(e.currentTarget).data('bs.' + this.type)
       if (!self) {
         self = new this.constructor(e.currentTarget, this.getDelegateOptions())
         $(e.currentTarget).data('bs.' + this.type, self)
       }
     }

     if (e) {
       self.inState.click = !self.inState.click
       if (self.isInStateTrue()) self.enter(self)
       else self.leave(self)
     } else {
       self.tip().hasClass('in') ? self.leave(self) : self.enter(self)
     }
   }

   Tooltip.prototype.destroy = function () {
     var that = this
     clearTimeout(this.timeout)
     this.hide(function () {
       that.$element.off('.' + that.type).removeData('bs.' + that.type)
       if (that.$tip) {
         that.$tip.detach()
       }
       that.$tip = null
       that.$arrow = null
       that.$viewport = null
     })
   }


   // TOOLTIP PLUGIN DEFINITION
   // =========================

   function Plugin(option) {
     return this.each(function () {
       var $this   = $(this)
       var data    = $this.data('bs.tooltip')
       var options = typeof option == 'object' && option

       if (!data && /destroy|hide/.test(option)) return
       if (!data) $this.data('bs.tooltip', (data = new Tooltip(this, options)))
       if (typeof option == 'string') data[option]()
     })
   }

   var old = $.fn.tooltip

   $.fn.tooltip             = Plugin
   $.fn.tooltip.Constructor = Tooltip


   // TOOLTIP NO CONFLICT
   // ===================

   $.fn.tooltip.noConflict = function () {
     $.fn.tooltip = old
     return this
   }

})(jQuery);
(function ($) {
  'use strict';

  // POPOVER PUBLIC CLASS DEFINITION
  // ===============================

  var Popover = function (element, options) {
    this.init('popover', element, options)
  }

  if (!$.fn.tooltip) throw new Error('Popover requires tooltip.js')

  Popover.VERSION  = '3.3.6'

  Popover.DEFAULTS = $.extend({}, $.fn.tooltip.Constructor.DEFAULTS, {
    placement: 'right',
    trigger: 'click',
    content: '',
    template: '<div class="popover" role="tooltip"><div class="arrow"></div><h3 class="popover-title"></h3><div class="popover-content"></div></div>'
  })


  // NOTE: POPOVER EXTENDS tooltip.js
  // ================================

  Popover.prototype = $.extend({}, $.fn.tooltip.Constructor.prototype)

  Popover.prototype.constructor = Popover

  Popover.prototype.getDefaults = function () {
    return Popover.DEFAULTS
  }

  Popover.prototype.setContent = function () {
    var $tip    = this.tip()
    var title   = this.getTitle()
    var content = this.getContent()

    $tip.find('.popover-title')[this.options.html ? 'html' : 'text'](title)
    $tip.find('.popover-content').children().detach().end()[ // we use append for html objects to maintain js events
      this.options.html ? (typeof content == 'string' ? 'html' : 'append') : 'text'
    ](content)

    $tip.removeClass('fade top bottom left right in')

    // IE8 doesn't accept hiding via the `:empty` pseudo selector, we have to do
    // this manually by checking the contents.
    if (!$tip.find('.popover-title').html()) $tip.find('.popover-title').hide()
  }

  Popover.prototype.hasContent = function () {
    return this.getTitle() || this.getContent()
  }

  Popover.prototype.getContent = function () {
    var $e = this.$element
    var o  = this.options

    return $e.attr('data-content')
      || (typeof o.content == 'function' ?
            o.content.call($e[0]) :
            o.content)
  }

  Popover.prototype.arrow = function () {
    return (this.$arrow = this.$arrow || this.tip().find('.arrow'))
  }


  // POPOVER PLUGIN DEFINITION
  // =========================

  function Plugin(option) {
    return this.each(function () {
      var $this   = $(this)
      var data    = $this.data('bs.popover')
      var options = typeof option == 'object' && option

      if (!data && /destroy|hide/.test(option)) return
      if (!data) $this.data('bs.popover', (data = new Popover(this, options)))
      if (typeof option == 'string') data[option]()
    })
  }

  var old = $.fn.popover

  $.fn.popover             = Plugin
  $.fn.popover.Constructor = Popover


  // POPOVER NO CONFLICT
  // ===================

  $.fn.popover.noConflict = function () {
    $.fn.popover = old
    return this
  }

})(jQuery);
(function(jQuery){ 
    if(jQuery.browser) return; 

    jQuery.browser = {}; 
    jQuery.browser.mozilla = false; 
    jQuery.browser.webkit = false; 
    jQuery.browser.opera = false; 
    jQuery.browser.msie = false; 

    var nAgt = navigator.userAgent; 
    jQuery.browser.name = navigator.appName; 
    jQuery.browser.fullVersion = ''+parseFloat(navigator.appVersion); 
    jQuery.browser.majorVersion = parseInt(navigator.appVersion,10); 
    var nameOffset,verOffset,ix; 

    // In Opera, the true version is after "Opera" or after "Version" 
    if ((verOffset=nAgt.indexOf("Opera"))!=-1) { 
    jQuery.browser.opera = true; 
    jQuery.browser.name = "Opera"; 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+6); 
    if ((verOffset=nAgt.indexOf("Version"))!=-1) 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+8); 
    } 
    // In MSIE, the true version is after "MSIE" in userAgent 
    else if ((verOffset=nAgt.indexOf("MSIE"))!=-1) { 
    jQuery.browser.msie = true; 
    jQuery.browser.name = "Microsoft Internet Explorer"; 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+5); 
    } 
    // In Chrome, the true version is after "Chrome" 
    else if ((verOffset=nAgt.indexOf("Chrome"))!=-1) { 
    jQuery.browser.webkit = true; 
    jQuery.browser.name = "Chrome"; 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+7); 
    } 
    // In Safari, the true version is after "Safari" or after "Version" 
    else if ((verOffset=nAgt.indexOf("Safari"))!=-1) { 
    jQuery.browser.webkit = true; 
    jQuery.browser.name = "Safari"; 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+7); 
    if ((verOffset=nAgt.indexOf("Version"))!=-1) 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+8); 
    } 
    // In Firefox, the true version is after "Firefox" 
    else if ((verOffset=nAgt.indexOf("Firefox"))!=-1) { 
    jQuery.browser.mozilla = true; 
    jQuery.browser.name = "Firefox"; 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+8); 
    } 
    // In most other browsers, "name/version" is at the end of userAgent 
    else if ( (nameOffset=nAgt.lastIndexOf(' ')+1) < 
    (verOffset=nAgt.lastIndexOf('/')) ) 
    { 
    jQuery.browser.name = nAgt.substring(nameOffset,verOffset); 
    jQuery.browser.fullVersion = nAgt.substring(verOffset+1); 
    if (jQuery.browser.name.toLowerCase()==jQuery.browser.name.toUpperCase()) { 
    jQuery.browser.name = navigator.appName; 
    } 
    } 
    // trim the fullVersion string at semicolon/space if present 
    if ((ix=jQuery.browser.fullVersion.indexOf(";"))!=-1) 
    jQuery.browser.fullVersion=jQuery.browser.fullVersion.substring(0,ix); 
    if ((ix=jQuery.browser.fullVersion.indexOf(" "))!=-1) 
    jQuery.browser.fullVersion=jQuery.browser.fullVersion.substring(0,ix); 

    jQuery.browser.majorVersion = parseInt(''+jQuery.browser.fullVersion,10); 
    if (isNaN(jQuery.browser.majorVersion)) { 
    jQuery.browser.fullVersion = ''+parseFloat(navigator.appVersion); 
    jQuery.browser.majorVersion = parseInt(navigator.appVersion,10); 
    } 
    jQuery.browser.version = jQuery.browser.majorVersion; 
})(jQuery);
(function(jQuery){
  jQuery.iUtil = {
      getPosition: function(e) {
          var x = 0;
          var y = 0;
          var restoreStyle = false;
          var es = e.style;
          if (jQuery(e).css('display') == 'none') {
              oldVisibility = es.visibility;
              oldPosition = es.position;
              es.visibility = 'hidden';
              es.display = 'block';
              es.position = 'absolute';
              restoreStyle = true
          }
          var el = e;
          while (el) {
              x += el.getBoundingClientRect().left + (el.currentStyle && !jQuery.browser.opera ? parseInt(el.currentStyle.borderLeftWidth) || 0: 0);
              y += el.getBoundingClientRect().top + (el.currentStyle && !jQuery.browser.opera ? parseInt(el.currentStyle.borderTopWidth) || 0: 0);
              el = el.offsetParent
          }
          el = e;
          while (el && el.tagName && el.tagName.toLowerCase() != 'body') {
              x -= el.scrollLeft || 0;
              y -= el.scrollTop || 0;
              el = el.parentNode
          }
          if (restoreStyle) {
              es.display = 'none';
              es.position = oldPosition;
              es.visibility = oldVisibility
          }
          return {
              x: x,
              y: y
          }
      },
      getPositionLite: function(el) {
          var x = 0,
          y = 0;
          while (el) {
              x += el.getBoundingClientRect().left || 0;
              y += el.getBoundingClientRect().top || 0;
              el = el.offsetParent
          }
          return {
              x: x,
              y: y
          }
      },
      getSize: function(e) {
          var w = jQuery.css(e, 'width');
          var h = jQuery.css(e, 'height');
          var wb = 0;
          var hb = 0;
          var es = e.style;
          if (jQuery(e).css('display') != 'none') {
              wb = e.offsetWidth;
              hb = e.offsetHeight
          } else {
              oldVisibility = es.visibility;
              oldPosition = es.position;
              es.visibility = 'hidden';
              es.display = 'block';
              es.position = 'absolute';
              wb = e.offsetWidth;
              hb = e.offsetHeight;
              es.display = 'none';
              es.position = oldPosition;
              es.visibility = oldVisibility
          }
          return {
              w: w,
              h: h,
              wb: wb,
              hb: hb
          }
      },
      getSizeLite: function(el) {
          return {
              wb: el.offsetWidth || 0,
              hb: el.offsetHeight || 0
          }
      },
      getClient: function(e) {
          var h,
          w,
          de;
          if (e) {
              w = e.clientWidth;
              h = e.clientHeight
          } else {
              de = document.documentElement;
              w = window.innerWidth || self.innerWidth || (de && de.clientWidth) || document.body.clientWidth;
              h = window.innerHeight || self.innerHeight || (de && de.clientHeight) || document.body.clientHeight
          }
          return {
              w: w,
              h: h
          }
      },
      getScroll: function(e) {
          var t,
          l,
          w,
          h,
          iw,
          ih;
          if (e && e.nodeName.toLowerCase() != 'body') {
              t = e.scrollTop;
              l = e.scrollLeft;
              w = e.scrollWidth;
              h = e.scrollHeight;
              iw = 0;
              ih = 0
          } else {
              if (document.documentElement && document.documentElement.scrollTop) {
                  t = document.documentElement.scrollTop;
                  l = document.documentElement.scrollLeft;
                  w = document.documentElement.scrollWidth;
                  h = document.documentElement.scrollHeight
              } else if (document.body) {
                  t = document.body.scrollTop;
                  l = document.body.scrollLeft;
                  w = document.body.scrollWidth;
                  h = document.body.scrollHeight
              }
              iw = self.innerWidth || document.documentElement.clientWidth || document.body.clientWidth || 0;
              ih = self.innerHeight || document.documentElement.clientHeight || document.body.clientHeight || 0
          }
          return {
              t: t,
              l: l,
              w: w,
              h: h,
              iw: iw,
              ih: ih
          }
      },
      getMargins: function(e, toInteger) {
          var el = jQuery(e);
          var t = el.css('marginTop') || '';
          var r = el.css('marginRight') || '';
          var b = el.css('marginBottom') || '';
          var l = el.css('marginLeft') || '';
          if (toInteger) return {
              t: parseInt(t) || 0,
              r: parseInt(r) || 0,
              b: parseInt(b) || 0,
              l: parseInt(l)
          };
          else return {
              t: t,
              r: r,
              b: b,
              l: l
          }
      },
      getPadding: function(e, toInteger) {
          var el = jQuery(e);
          var t = el.css('paddingTop') || '';
          var r = el.css('paddingRight') || '';
          var b = el.css('paddingBottom') || '';
          var l = el.css('paddingLeft') || '';
          if (toInteger) return {
              t: parseInt(t) || 0,
              r: parseInt(r) || 0,
              b: parseInt(b) || 0,
              l: parseInt(l)
          };
          else return {
              t: t,
              r: r,
              b: b,
              l: l
          }
      },
      getBorder: function(e, toInteger) {
          var el = jQuery(e);
          var t = el.css('borderTopWidth') || '';
          var r = el.css('borderRightWidth') || '';
          var b = el.css('borderBottomWidth') || '';
          var l = el.css('borderLeftWidth') || '';
          if (toInteger) return {
              t: parseInt(t) || 0,
              r: parseInt(r) || 0,
              b: parseInt(b) || 0,
              l: parseInt(l) || 0
          };
          else return {
              t: t,
              r: r,
              b: b,
              l: l
          }
      },
      getPointer: function(event) {
          var x = event.clientX || (event.clientX + (document.documentElement.scrollLeft || document.body.scrollLeft)) || 0;
          var y = event.clientY || (event.clientY + (document.documentElement.scrollTop || document.body.scrollTop)) || 0;
          return {
              x: x,
              y: y
          }
      },
      traverseDOM: function(nodeEl, func) {
          func(nodeEl);
          nodeEl = nodeEl.firstChild;
          while (nodeEl) {
              jQuery.iUtil.traverseDOM(nodeEl, func);
              nodeEl = nodeEl.nextSibling
          }
      },
      purgeEvents: function(nodeEl) {
          jQuery.iUtil.traverseDOM(nodeEl, 
          function(el) {
              for (var attr in el) {
                  if (typeof el[attr] === 'function') {
                      el[attr] = null
                  }
              }
          })
      },
      centerEl: function(el, axis) {
          var clientScroll = $.iUtil.getScroll();
          var windowSize = $.iUtil.getSize(el);
          if (!axis || axis == 'vertically') $(el).css({
              top: clientScroll.t + ((Math.max(clientScroll.h, clientScroll.ih) - clientScroll.t - windowSize.hb) / 2) + 'px'
          });
          if (!axis || axis == 'horizontally') $(el).css({
              left: clientScroll.l + ((Math.max(clientScroll.w, clientScroll.iw) - clientScroll.l - windowSize.wb) / 2) + 'px'
          })
      },
      fixPNG: function(el, emptyGIF) {
          var images = $('img[@src*="png"]', el || document),
          png;
          images.each(function() {
              png = this.src;
              this.src = emptyGIF;
              this.style.filter = "progid:DXImageTransform.Microsoft.AlphaImageLoader(src='" + png + "')"
          })
      }
  }; [].indexOf || (Array.prototype.indexOf = function(v, n) {
      n = (n == null) ? 0: n;
      var m = this.length;
      for (var i = n; i < m; i++) if (this[i] == v) return i;
      return - 1
  });
  jQuery.iFisheye = {
      build: function(options) {
          return this.each(function() {
              var el = this;
              el.fisheyeCfg = {
                  items: jQuery(options.items, this),
                  container: jQuery(options.container, this),
                  pos: jQuery.iUtil.getPosition(this),
                  itemWidth: options.itemWidth,
                  itemsText: options.itemsText,
                  proximity: options.proximity,
                  valign: options.valign,
                  halign: options.halign,
                  maxWidth: options.maxWidth
              };
              jQuery.iFisheye.positionContainer(el, 0);
              jQuery(window).bind('resize', 
              function() {
                  el.fisheyeCfg.pos = jQuery.iUtil.getPosition(el);
                  jQuery.iFisheye.positionContainer(el, 0);
                  jQuery.iFisheye.positionItems(el)
              });
              jQuery.iFisheye.positionItems(el);
              // el.fisheyeCfg.items.bind('mouseover', 
              // function() {
              //     jQuery(el.fisheyeCfg.itemsText, this).get(0).style.display = 'block'
              // }).bind('mouseout', 
              // function() {
              //     jQuery(el.fisheyeCfg.itemsText, this).get(0).style.display = 'none'
              // });
              jQuery(document).bind('mousemove', 
              function(e) {
                  var pointer = jQuery.iUtil.getPointer(e);
                  if(!pointer)return false;
                  var toAdd = 0;
                  if (el.fisheyeCfg.halign && el.fisheyeCfg.halign == 'center') var posx = pointer.x - el.fisheyeCfg.pos.x - (el.offsetWidth - el.fisheyeCfg.itemWidth * el.fisheyeCfg.items.size()) / 2 - el.fisheyeCfg.itemWidth / 2;
                  else if (el.fisheyeCfg.halign && el.fisheyeCfg.halign == 'right') var posx = pointer.x - el.fisheyeCfg.pos.x - el.offsetWidth + el.fisheyeCfg.itemWidth * el.fisheyeCfg.items.size();
                  else var posx = pointer.x - el.fisheyeCfg.pos.x;
                  var posy = Math.pow(pointer.y - el.fisheyeCfg.pos.y - el.offsetHeight / 2, 2);
                  el.fisheyeCfg.items.each(function(nr) {
                      distance = Math.sqrt(Math.pow(posx - nr * el.fisheyeCfg.itemWidth, 2) + posy);
                      distance -= el.fisheyeCfg.itemWidth / 2;
                      distance = distance < 0 ? 0: distance;
                      distance = distance > el.fisheyeCfg.proximity ? el.fisheyeCfg.proximity: distance;
                      distance = el.fisheyeCfg.proximity - distance;
                      extraWidth = el.fisheyeCfg.maxWidth * distance / el.fisheyeCfg.proximity;
                      this.style.width = el.fisheyeCfg.itemWidth + extraWidth + 'px';
                      this.style.height = this.style.width;
                      this.style.left = el.fisheyeCfg.itemWidth * nr + toAdd + 'px';
                      this.style.marginTop = '-'+(( extraWidth)/2)+'px';
                      // this.style.marginBottom = (el.fisheyeCfg.itemWidth + extraWidth)/2+'px';

                      toAdd += extraWidth
                  });
                  jQuery.iFisheye.positionContainer(el, toAdd)
              })
          })
      },
      positionContainer: function(el, toAdd) {
          // if (el.fisheyeCfg.halign) if (el.fisheyeCfg.halign == 'center') el.fisheyeCfg.container.get(0).style.left = (el.offsetWidth - el.fisheyeCfg.itemWidth * el.fisheyeCfg.items.size()) / 2 - toAdd / 2 + 'px';
          // else if (el.fisheyeCfg.halign == 'left') el.fisheyeCfg.container.get(0).style.left = -toAdd / el.fisheyeCfg.items.size() + 'px';
          // else if (el.fisheyeCfg.halign == 'right') el.fisheyeCfg.container.get(0).style.left = (el.offsetWidth - el.fisheyeCfg.itemWidth * el.fisheyeCfg.items.size()) - toAdd / 2 + 'px';
          // el.fisheyeCfg.container.get(0).style.width = el.fisheyeCfg.itemWidth * el.fisheyeCfg.items.size() + toAdd + 'px'
      },
      positionItems: function(el) {
          el.fisheyeCfg.items.each(function(nr) {
              this.style.width = el.fisheyeCfg.itemWidth + 'px';
              this.style.left = el.fisheyeCfg.itemWidth * nr + 'px'
          })
      }
  };
})(jQuery);
jQuery.fn.Fisheye = jQuery.iFisheye.build;

/*sortable*/
(function($){  
  /*
  function getSelectionField(e) {
    var selection = '';
    selection = getIeSelection(e);
    if (selection == '') {
      selection = getFireFoxSelection(e);
    }
    return selection;
  }
  
  function getIeSelection(e) {
    if (window.getSelection) {
      return window.getSelection().toString();
    } else if (document.getSelection) {
      return document.getSelection();
    } else if (document.selection) {
      return document.selection.createRange().text;
    }
  }

  function getFireFoxSelection(e) {
    if (e.selectionStart != undefined && e.selectionEnd != undefined) {
      var start = e.selectionStart;
      var end = e.selectionEnd;

      return e.value.substring(start, end);
    } else {
      return "";
    }
  } 
  */
  function draggable(el,opts){
    //debugger;
    var sysdrag;
    opts.position = opts.position || "relative";
    var el_ = el;
    el.bind("dragstart",function(){
      sysdrag = true;
      //alert(1);
    });

    el.addClass("unselectable");
    var ox, oy,tx,ty;
    var dragging = false;
    function onmove(evt){
      if(sysdrag) return ;
      var dx = evt.pageX - ox, dy = evt.pageY - oy;
      if(!dragging){
        if(Math.abs(dx) >= 5 || Math.abs(dy) >= 5){         
          //debugger;
          //console.log("dragging");
          if(!opts.beforeDrag || opts.beforeDrag(evt,el)!==false){
            dragging = true;
            onDrag(evt);
          }       
        }
      }
      if(!dragging) return ;
      
      el.css("left",(tx+dx) + "px").css("top",(ty+dy) + "px");
      if(opts.onMove){
        opts.onMove(evt,el);
      }
    }
    
    function onup(evt){
      sysdrag = false;
      
      $(document).unbind("mousemove",onmove);
      $(document).unbind("mouseup",onup);
      
      if(dragging){
        el.css("cursor","auto");
        if(opts.onDrop){
          opts.onDrop(evt,el);
        }
      }
      
      //el_.removeClass("unselectable");
    }
    
    function onDrag(evt){
      var offset;
      if(opts.cloneOnDrag && (typeof opts.cloneOnDrag != "function" || opts.cloneOnDrag(el_))){
        el = el_.clone(); 
        //el_.before(el);
        $(document.body).append(el);
        opts.position = "absolute";
        offset = el_.offset();
      }

      if(opts.position == "absolute"){
        if(!offset) offset = el_.position();
        //debugger;
        el.css("top",offset.top+"px")
           .css("left",offset.left+"px")
           .css("height",el_.height()+"px")
           .css("width",el_.width()+"px");
      }
      
      el.css("position",opts.position).css("cursor","move").css("z-index","110");
          
      tx = parseFloat(el.css("left"));
      ty = parseFloat(el.css("top")); 
      if(opts.onDrag){
        opts.onDrag(evt,el);
      }
    };
    
    el.mousedown(function(evt){ 
      el = el_;
      el_.data("float",el_.css("float"));
      dragging = false;
      ox = evt.pageX;
      oy = evt.pageY;
      //el.addClass("unselectable");
      
      setTimeout(function(){        
        $(document).mousemove(onmove);      
        $(document).mouseup(onup);
      },10);      
    });
  }
  
  function dragonly(that,f) { 
    
    var sx,sy,pos,target = f || that;
    var move_action = function(evt){
      var dx = evt.clientX - sx,
        dy = evt.clientY - sy;
      $(target).css({
        left : pos.left + dx +"px",
        top : pos.top + dy +"px"
      });
    };
    
    var up_action = function(){
      $(document.body).unbind("mousemove",move_action).unbind("mouseup",up_action);
    };
    
    that.mousedown(function(evt){
      sx = evt.clientX;   
      sy = evt.clientY;

      pos = {
        left : parseInt($(target).css("left")),
        top : parseInt($(target).css("top"))
      };

      $(document.body).mousemove(move_action).mouseup(up_action);
    });
    
  };
  
  var ghost;  
  function sortable(el,opt){    
    //var c = 0;
    el.drags({
      position:'absolute',
      beforeDrag : opt.beforeDrag,
      cloneOnDrag : opt.cloneOnDrag,
      onDrag : function(evt,el){
        if(ghost){
          //debugger;
          var _el = ghost.data("_el");
          if(_el){
            ghost.before(_el);
            _el.css("position","").css("left","0px").css("top","0px");
          }
          ghost.remove();         
        }
        ghost = el.ghost();
        ghost.css("float",el.data("float"));
        ghost.data("_el",el);
        
        if(!opt.cloneOnDrag){
          el.before(ghost);
        }
        
        
        if(opt.onDrag){
          opt.onDrag(evt,el,ghost);
        }       
      },
      
      onMove : function(evt,el){  
        //console.log("moving");
        var px = evt.pageX,py = evt.pageY;
        //console.log(px+"-"+py);
        var found = false;

        var posg = ghost.offset();  
        if(px>=posg.left && px<=posg.left+ghost.width()
            && py>=posg.top && py<=posg.top+ghost.height()){
          found = true;
        }
        
        //console.log("f1"+found);
        
        if(!found && opt.list){
          opt.list.each(function(){
            if(el[0] != this){
              var pos = $(this).offset();           
              if(px>=pos.left && px<=pos.left+$(this).width()
                  && py>=pos.top && py<=pos.top+$(this).height()){
                if(!opt.onDragOver || opt.onDragOver(evt,$(this),ghost)!==false){
                  if($(this).prev()[0] == ghost[0]){
                    $(this).after(ghost);
                  }else{
                    $(this).before(ghost);
                  }
                }
                found = true;
                return false;
              }
              
            }
          });
        }
        
        //console.log("f2"+found);
        
        if(!found && opt.targets){
          opt.targets.each(function(){ 
            var pos = $(this).offset();           
            if(px>=pos.left && px<=pos.left+$(this).width()
                && py>=pos.top && py<=pos.top+$(this).height()){
              if(!opt.onDragOver || opt.onDragOver(evt,$(this),ghost)!==false){
                $(this).append(ghost);
              }
              found = true;
              return false;
            }
          });
        }
      
        
        if(opt.onMove){
          opt.onMove(evt,el,ghost);
        }
      },
      onDrop : function(evt,el){
        ghost.before(el);
        if(ghost.parent().length==0 && opt.cloneOnDrag){
          el.remove();
        }       
        el.css("position","").css("left","0px").css("top","0px");
        ghost.remove();
        if(opt.onDrop){
          opt.onDrop(evt,el,opt);
        }
      }
    });
  }
  
  //debugger;
  $.extend($.fn,{
    drags : function(opts){
      this.each(function(){
        draggable($(this),opts || {});      
      });
    },
    ghost : function(){
      //console.log($(this).css("margin-left"));
      var ghost = $("<div></div>");
      //var offset = $(this).position();
      ghost/*.css("top",offset.top+"px")
         .css("left",offset.left+"px")*/
         .css("height",$(this).outerHeight()+"px")
         .css("width",$(this).outerWidth()+"px")
         .css("margin-left",$(this).css("margin-left"))
         .css("margin-right",$(this).css("margin-right"))
         .css("margin-top",$(this).css("margin-top"))
         .css("margin-bottom",$(this).css("margin-bottom"));
         
      
      return ghost;
    },
    sorts : function(opts){
      opts = opts ||{};
      opts.list = this;
      this.each(function(){
        //onDrag($(this),opts); 
        sortable($(this),opts);
      });
      
      return {append:function(els){
        //debugger;       
        els.each(function(){
          opts.list.push(this);
          sortable($(this),opts);
        });       
        //sortable(els,opts);
      }};
    },
    dragonly : function(f){
      dragonly($(this),f);  
    }
  });
  
})(jQuery);



$.fn.serializeJson=function(){  
    var serializeObj={};
    var seri = this.serialize(); 
    $(this.serializeArray()).each(function(){
        if(((seri.split(this.name)).length-1)>1){
          if(!serializeObj[this.name])serializeObj[this.name]=[];
          serializeObj[this.name].push(this.value);
        }else{
          serializeObj[this.name]=this.value;  
        }
    }); 
    return serializeObj;  
};
/**
 * 以下 bind mousemove方法，绑定在document上时会与鱼眼效果冲突，因此绑定在body上边
 */
/**
 * draggable拖动方法
 * by Wesson
 * @param  {[type]} options [description]
 * @return {[type]}         [description]
 */
jQuery.fn.wsdraggable = function(options){
    return this.each(function(){
  var target = $(this);
  if(options&&options.handle){
    target = $(this).find(options.handle);
  }
  var _that = $(this);
  var t = _that,zindex;
  // target.hover(function(){$(this).css("cursor","move");},function(){$(this).css("cursor","default");})
  var x,y,flag = false;
  _that.find('.modal-dialog').mousedown(function(){
    var t = $(this);
    if(t.hasClass('maxty'))return false;
  })
  // _that.find('.modal-dialog').click(function(){
  //   console.log("fasfdasdf")
  //   var t = $(this);
  //   t.css({"z-index":2000})
  //   t.find(".modal-dialog").css({'opacity':'0.3',"position":"absolute",'z-index':2000});
  //   var modals = [];
  //   $(".modal.in").each(function(){
  //       var z = parseInt($(this).find(".modal-dialog").css("z-index"));
  //       // if(z==0)return false;
  //       modals.push({
  //           name:$(this).attr("id"),
  //           zindex:z
  //       })
  //   })
  //   modals.sort(function(a,b){
  //       return a.zindex>b.zindex?1:-1;
  //   })
  //   // console.log(modals);
  //   for(var i =0;i<modals.length;i++){
  //     $("#"+modals[i].name).css("z-index",i*5);
  //     $("#"+modals[i].name).find(".modal-dialog").css("z-index",i*5);
  //   }
  // })
  target.mousedown(function(e){//e鼠标事件
    e.stopPropagation();
    if($(e.target).parents("button").length==0){
    
      // t = $(this).parents(".modal");
      if(t.find('.modal-dialog').hasClass('maxty'))return false;
      zindex = t.find(".modal-dialog").css("z-index");
        x = e.clientX - t.find(".modal-dialog")[0].offsetLeft;
        y = e.clientY - t.find(".modal-dialog")[0].offsetTop;
        $("body").mousemove(function(ev){//绑定鼠标的移动事件，因为光标在DIV元素外面也要有效果，所以要用doucment的事件，而不用DIV元素的事件
              if(!flag){
                  t.addClass('Moving');
                  flag = true;
                  $(this).addClass('unselection');
                  $(document).bind('selectstart',function(){return false;});
                  t.css({"z-index":2000})
                  t.find(".modal-dialog").css({'opacity':'0.3',"position":"absolute",'z-index':2000});
              }
              var _x = ev.clientX - x;//获得X轴方向移动的值
              var _y = ev.clientY - y;//获得Y轴方向移动的值
              if(t.hasClass('modal')){
                // _y = t.attr("id")=="realrightmodal"?(_y-50):(t.attr("id").indexOf("_manage")>-1?_y:(_y-110));
                // t.css("z-index",2000);
                t.find(".modal-dialog").css({'left':_x+"px",'top':_y+"px"})
              }else{
                t.css({'left':_x+"px",'top':_y+"px"});
              }
        });
      }  
  });

  $("body").mouseup(function(event){
        $(this).unbind("mousemove");
        $(this).removeClass('unselection');
        if(t&&flag){
            t.removeClass("Moving");
            var modals = [];
            $(".modal.in").each(function(){
                var z = parseInt($(this).find(".modal-dialog").css("z-index"));
                // if(z==0)return false;
                modals.push({
                    name:$(this).attr("id"),
                    zindex:z
                })
            })
            modals.sort(function(a,b){
                return a.zindex>b.zindex?1:-1;
            })
            for(var i =0;i<modals.length;i++){
              $("#"+modals[i].name).css("z-index",i*5);
              if(modals[i].name.indexOf("appmodal")>0&&modals[i].name.indexOf("_")==-1){
                $("#"+modals[i].name).find(".modal-dialog").css("z-index",i*5);
              }else{
                $("#"+modals[i].name).find(".modal-dialog").css("z-index",(1050+i*5));
              }
            }
            if(t.hasClass('modal')){
              t.find(".modal-dialog").css({'opacity':''})
            }else{
              t.css({'opacity':''});
            }
            flag = false;
        }
  })
  })
}
/**
 * resizable改变大小方法
 * by Wesson
 * @param  {[type]} argument [description]
 * @return {[type]}          [description]
 */
jQuery.fn.wsresizable = function(argument) {
    // return this.each(function(){

    // })
  var t,target = $(this).hasClass('modal')?$(this).find(".modal-dialog"):$(this);
  var box  = $(this).hasClass('modal')?$(this).find(".modal-content"):$(this);
  var heng = $('<div class="heng"></div>');
  var shu = $('<div class="shu"></div>');
  var youxiajiao = $('<div class="youxiajiao"></div>');

  // if($(this).find(".heng").length==1)return false;
  box.append(heng).append(shu).append(youxiajiao);
  
  var resiflag = false;
  $(document).delegate(".shu","mousedown",function(e){//e鼠标事件  横向移动
     target = $(this).parents(".modal-dialog");
     if(target.hasClass('maxty'))return false;
     target.removeClass("dialog-init");
      var l = target[0].getBoundingClientRect().left,t = target[0].getBoundingClientRect().top;
      target.css({
        position:"absolute",
        left:l+"px",
        // top:t+"px"
      })
      target.removeClass("dialog-init");
      t = $(this).parents(".modal")
      resiflag = true;
     var wx = target[0].getBoundingClientRect().left;
     var height = target[0].offsetHeight;
      $("body").bind("mousemove",function(ev){//绑定鼠标的移动事件，因为光标在DIV元素外面也要有效果，所以要用doucment的事件，而不用DIV元素的事件
          $(this).addClass('unselection');
          $(document).bind('selectstart',function(){return false;});
          var _x = ev.clientX-wx;
          if(_x<300)return false;
            target.css({"width":_x+"px",height:height+"px"});
            t.find(".modal-content").css({"width":_x+"px",height:height+"px"});    
      });
  });
  $(document).delegate(".heng","mousedown",function(e){//e鼠标事件  竖向移动
    target = $(this).parents(".modal-dialog");
    if(target.hasClass('maxty'))return false;
    var l = target[0].getBoundingClientRect().left,t = target[0].getBoundingClientRect().top;
    target.css({
        position:"absolute",
        left:l+"px",
        // top:t+"px"
    })
    target.removeClass("dialog-init");
    t = $(this).parents(".modal")
    resiflag = true;
     var wy = target[0].getBoundingClientRect().top;
     var wx = target[0].getBoundingClientRect().left;
     var width = target[0].offsetWidth;
     var height = target[0].offsetHeight;
      $("body").bind("mousemove",function(ev){//绑定鼠标的移动事件，因为光标在DIV元素外面也要有效果，所以要用doucment的事件，而不用DIV元素的事件
          $(this).addClass('unselection');
          $(document).bind('selectstart',function(){return false;});
          var _y = ev.clientY - wy;//获得Y轴方向移动的值
          if(_y<300)return false;
          target.css({"height":_y+"px","width":width+"px"});    
          t.find(".modal-content").css({"height":_y+"px","width":width+"px"});
                 
      });
  });
  $(document).delegate(".youxiajiao","mousedown",function(e){//e鼠标事件 斜下方移动
    target = $(this).parents(".modal-dialog");
    if(target.hasClass('maxty'))return false;
    target.removeClass("dialog-init");
    var l = target[0].getBoundingClientRect().left,t = target[0].getBoundingClientRect().top;
      target.css({
        position:"absolute",
        left:l+"px",
        // top:t+"px"
      })
      target.removeClass("dialog-init");
      t = $(this).parents(".modal")
      resiflag = true;
     var wx = target[0].getBoundingClientRect().left;
     var wy = target[0].getBoundingClientRect().top;
      $("body").bind("mousemove",function(ev){//绑定鼠标的移动事件，因为光标在DIV元素外面也要有效果，所以要用doucment的事件，而不用DIV元素的事件
          $(this).addClass('unselection');
          $(document).bind('selectstart',function(){return false;});
          var _x = ev.clientX - wx;//获得X轴方向移动的值
          var _y = ev.clientY - wy;//获得Y轴方向移动的值
          if(_x<300&&_y<300)return false;
          target.css({"width":_x+"px","height":_y+"px"});
          t.find(".modal-content").css({"width":_x+"px","height":_y+"px"});
      });
  });

  $("body").mouseup(function(){
    if(resiflag){
      function getheight(it){
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop-110;
      }
      var $table = target.find(".fixed-table-body table");
      if($table.length>0){
        $table.each(function(){
          var _that = $(this);
          if(!_that.attr("data-show-refresh"))return false;
          _that.bootstrapTable('resetView', {
              height: getheight(_that)
          });
        })
      }
      $(this).removeClass('unselection');
        // target.addClass("dialog-init");
      $(this).unbind("mousemove");
      resiflag = false;
    }
  })
}