/**
*socket
**/
  function socket(){}
  socket.prototype.connect = function(param){
    var port = window.location.port;
    if(port==90){
        var ws = new ReconnectingWebSocket("ws://42.51.161.236:91/websocket", null, {debug: true, reconnectInterval: 5000});
    }else{
        //var ws = new ReconnectingWebSocket("ws://42.51.161.236:91/websocket", null, {debug: true, reconnectInterval: 5000});
        var ws = new ReconnectingWebSocket("ws://"+window.location.host+"/websocket", null, {debug: true, reconnectInterval: 5000});
    }
    this.ws = ws;
  }

  socket.prototype.emit = function(senddata){
    // console.log("((((((((((((((");
    //   console.log(senddata)
    this.ws.onopen = function(){
      // console.log("************")
      // console.log(senddata)
      this.ws.send(senddata);
    }
  }  
  var soc = new socket();
  soc.connect();

  soc.ws.onmessage = function(e){
    var msg = JSON.parse(e.data);
    // console.log(msg);
    if(msg['NOTIFY']){
      winnotify.$set("show",true);
      var arr = winnotify.$get("message");
      arr.push(msg['NOTIFY']);
      winnotify.$set("message",arr);
    }
    var app = localStorage.getItem("currentapp");
    if(window.tabss&&window.tabss[app]){
      var data = JSON.parse(e.data);
      // console.log(data)
      var srvs = JSON.parse(JSON.stringify(tabss[app].$get("srvs")));
      for(var i =0;i<srvs.length;i++){
          if(data["Zones_"+srvs[i].uuid]){
            if(data["Zones_"+srvs[i].uuid].progress){
              srvs[i]["progress"] = data["Zones_"+srvs[i].uuid];
              srvs[i]["progress"]["width"] = srvs[i]["progress"].progress.split("/")[0]/srvs[i]["progress"].progress.split("/")[1]*100;
            }else{
              srvs[i]["progress"] = null;
            }
          }
          if(data["monitor-"+srvs[i].uuid]){
            srvs[i]["health"] = data["monitor-"+srvs[i].uuid].health;
          }
      }
      // console.log(srvs)
      tabss[app].$set("srvs",srvs);
    }

    for(var o in msg){
      if(o.indexOf("Assets")>-1){
        $(app).find("#hosttable tr").each(function(){
          var td = $(this).find("td:eq(1)");
          var id = td.find("input[name='uuid']").val();
          if(o.split("Assets_")[1]==id){
            var ms = msg[o];
            if(!ms.finish){
              var percent = parseFloat(ms.progress.split("/")[0])/parseInt(ms.progress.split("/")[1])*100;
              var dom ='<div class="overlay" style="position: absolute;height: 100%;right: 0;top: 0;width: 100%;background-color: rgba(0,0,0,0.3);left: 0;bottom: 0;"></div>'; 
                     //  '<div class="progress progress-animated progress-striped">'+
                     //    '<div style="width:'+percent+'%" class="progress-bar progress-bar-success" data-percentage="100" >'+percent+'%</div>'+
                     // ' </div>'
              td.css("porition","relative").append(dom);
            }else{
              td.find(".overlay").remove();
            }
          }
        })
      }
    }


  }

  soc.ws.onclose = function(code, reason){
    console.log(code, reason);
    // soc.ws.refresh();
  }


/**
*加载app中tab页面
**/
  function modaltpl(key,title){
    return [
        '<div>',
        '<button class="btn btn-default" id="<%common%>_'+key+'">'+title[0]+'</button>',
        '<modal id="<%common%>_'+key+'_manage" :showp.sync="platzooms[\''+key+'\']" effect="zoom">',
          '<div slot="modal-header" class="modal-header">',
              '<button type="button" class="modal-btn close" @click="closeplat($event,\''+key+'\')" data-dismiss="modal" aria-label="Close"><span class="glyphicon glyphicon-remove"></span></button>',
              '<button type="button" class="modal-btn maxify" @click="maxplat($event,\''+key+'\')">',
              '<span  v-if="!platismax[\''+key+'\']" class="glyphicon glyphicon-unchecked"></span>',
             ' <span v-if="platismax[\''+key+'\']" class="glyphicon glyphicon-modal-window"></span></button>',
              '<button type="button" class="modal-btn minify" @click="minplat($event,\''+key+'\')"><span  class="glyphicon glyphicon-minus"></span></button>',
            '<h4 class="modal-title">',
                '<b><%commontitle%>-'+title[1]+'</b>',
            '</h4>',
          '</div>',
          '<div slot="modal-body" class="modal-body">',
              
          '</div>',
        '</modal>',
        '</div>'
      ].join('');
  }
  function cmdbmodaltpl(key,title){
    return [
        '<div>',
        '<button class="btn btn-default"  @click="show($event,'+key+')" id="appmodal_'+key+'">'+title[0]+'</button>',
        '<modal id="appmodal_'+key+'" :show.sync="zooms[\''+key+'\']" effect="zoom">',
          '<div slot="modal-header" class="modal-header">',
              '<button type="button" class="modal-btn close" @click="close($event,\''+key+'\')" data-dismiss="modal" aria-label="Close"><span class="glyphicon glyphicon-remove"></span></button>',
              '<button type="button" class="modal-btn maxify" @click="max($event,\''+key+'\')">',
              '<span  v-if="!ismax[\''+key+'\']" class="glyphicon glyphicon-unchecked"></span>',
             ' <span v-if="ismax[\''+key+'\']" class="glyphicon glyphicon-modal-window"></span></button>',
              '<button type="button" class="modal-btn minify" @click="min($event,\''+key+'\')"><span  class="glyphicon glyphicon-minus"></span></button>',
            '<h4 class="modal-title">',
                '<b>'+title[1]+'</b>',
            '</h4>',
          '</div>',
          '<div slot="modal-body" class="modal-body">',
              
          '</div>',
        '</modal>',
        '</div>'
      ].join('');
  }
  function loadtab(id){
    var tabs = VueStrap.tabset,
        tab = VueStrap.tab;
      Vue.component('tabs',tabs);
      Vue.component('tab',tab);
      // var select = VueStrap.select,
      //     option = VueStrap.option;

        // Vue.component('vSelect',select);
        // Vue.component('vOption',option);
      window.tabss = window.tabss||{};
      // console.log(tabss)
      var commonapp = localStorage.getItem("currentapp").split("#")[1];
      var appid = localStorage.getItem("currentappid");
      // if(tabss[id]){
      //   tabss[id].$destroy(false);
      // }
      console.log(id);
      tabss[id] = new Vue({
        el:id,
        data:function(){
          return {
            fruitOptions:[
              {value:'search', label:'服务器'},
              {value:'banana', label:'游戏区服'},
              {value:'cherry', label:'任务日志'},
              {value:'orange', label:'监控'}
            ],
            arr:[],
            srvs:[],
            page_size:84,//区服每页显示几个
            pages:1,//区服总页数
            current_page:1,//区服当前页数
            currentsrvurl:"",//当前分页的url
            tabs:[
              {key:"__all__",value:"所有区服"},
            ],
            platidfortab:"",
            currentregion:"__all__",//当前的tab
            loadsrvurl:"",//加载所有区服的地址
            ifall:false,
            srvcmds:[],
            hostcmds:[],
            selectSrv:[],
            selectedhost:[],
            selectSrvurl:"",
            selecthosturl:"",
            envs:1,
            istimeout:false,

            /*日志步骤*/
            steps:[],
            //以下是关于tab内的弹窗
            common:commonapp,
            commontitle:$("#"+commonapp).find(".modal-title:first").text(),
            platcreateurls:{
              "createregion":"",
              "addcmd":"/ops/"+appid+"/script/create",
              "updatecmd":"",
              "addrole":"/"+appid+"/roles/create",
              "updateapprole":"",
              "addplattogame":"/ops/"+appid+"/plat/create",
              "addworkflow":"/ops/"+appid+"/workflow/create",
              "updateworkflow":""
            },
            platzooms:{
              "createregion":false,
              "addcmd":false,
              "updatecmd":false,
              "addrole":false,
              "updateapprole":false,
              "addplattogame":false,
              "addworkflow":false,
              "updateworkflow":false,
            },
            platismax:{
              "createregion":false,
              "addcmd":false,
              "updatecmd":false,
              "addrole":false,
              "updateapprole":false,
              "addplattogame":false,
              "addworkflow":false,
              "updateworkflow":false,
            },
            platinit_val:[],

            randomcolor:['danger','primary','warning','success','info'],
            addchart:false,
            widgets:[],
            widgetSelected:[],
            block:[],
            pie:[],
            line:[],
            column:[],

            deletebtn:{},
            selecteddel:{},
          }
        },
        ready:function(){
            var _this = this;
            if(!_this.target){
              _this.target = {};
            }
            var modals = [];
            $(".modal.in").each(function(){
                var z = parseInt($(this).find(".modal-dialog").css("z-index"));
                modals.push(z);
            })
            var zindex = Math.max.apply(null,modals);

            var urls = this.platcreateurls;
            for(var u in urls){
              zindex+=1;
              $("#"+_this.common+"_"+u+"_manage").find(".modal-dialog").css("z-index",zindex);
              $("#"+_this.common+"_"+u+"_manage").appendTo($("body"));
              _this.target[u] = $("#"+_this.common+"_"+u+"_manage").find(".modal-dialog");
            }

            GCR.modals.ready();
        },
        methods:{
          selectall:function(){
            var t = this;
            t.ifall = !t.ifall;
            if(t.ifall){
              $("#"+commonapp).find("#srv-datas li").addClass('srv-selected');
            }else{
              $("#"+commonapp).find("#srv-datas li").removeClass('srv-selected');
            }
          },
          clickSrv:function(event,srv){
            if(srv.progress&&!srv.progress.finish){
              return false;
            }
            var t = this;
            var target = event.target.nodeName=="LI"?$(event.target):$(event.target).parents("li");
            if(target.hasClass("srv-selected")){
              for(var i=0;t.selectSrv.length;i++){
                if(t.selectSrv[i].sid==srv.sid){
                  t.selectSrv.splice(i,1);
                  break;
                }
              }
              target.removeClass("srv-selected");
            }else{
              console.log(event)
              if(event.shiftKey){//shift多选
                 $("#"+commonapp).find("#srv-datas li").css({
                     '-moz-user-select': 'none', 
                     '-webkit-user-select': 'none',
                     '-ms-user-select': 'none',
                     '-khtml-user-select': 'none',
                     'user-select': 'none',
                })
                var start = t.srvs.indexOf(t.selectSrv[t.selectSrv.length-1]);
                var len = t.srvs.indexOf(srv);
                var hs = {};
                for(var i=0;i<t.selectSrv.length;i++){
                  hs[t.selectSrv[i].uuid] = t.selectSrv[i].uuid;
                }
                for(var i=start;i<(len+1);i++){
                  if(!hs[t.srvs[i].uuid]){
                    t.selectSrv.push(t.srvs[i]);
                    $("#"+commonapp).find("#srv-datas").find("#"+t.srvs[i].uuid).addClass('srv-selected');
                  }
                }
              }else{
                target.addClass('srv-selected');
                this.selectSrv.push(srv);
              }
              
            }
            
          },
          loadtabsrv:function(event,tab){
            var t = this;
            t.$set("currentregion",tab.key);
            if(tab.key=="__all__"){
              t.$set("currentsrvurl",t.loadsrvurl);
              $.ajax({
                url:t.loadsrvurl+"?page_size="+t.page_size+"&page="+1,
                type:"get",
                dataType:"json",
                success:function(datas){
                  t.$set("srvs",datas.results);
                }
              })
            }else{
               t.$set("currentsrvurl",tab.url);
              $.ajax({
                url:tab.url+"&page_size="+t.page_size+"&page="+1,
                type:"get",
                dataType:"json",
                success:function(datas){
                  t.$set("pages",Math.ceil(datas.count/parseInt(t.page_size)));
                  t.$set("srvs",datas.results);
                }
              })
            }
          },
          loadpagesrv:function(page){
            var t = this;
            var fuhao = t.currentsrvurl.indexOf("?")>-1?"&":"?";
            $.ajax({
              url:t.currentsrvurl+fuhao+"page_size="+t.page_size+"&page="+page,
              type:"get",
              dataType:"json",
              success:function(datas){
                t.$set("current_page",page);
                t.$set("srvs",datas.results);
              }
            })
          },
          loadpresrv:function(){
            var t = this;
            var fuhao = t.currentsrvurl.indexOf("?")>-1?"&":"?";
            if(t.current_page==1){
              return false;
            }else{
                $.ajax({
                  url:t.currentsrvurl+fuhao+"page_size="+t.page_size+"&page="+(parseInt(t.current_page)-1),
                  type:"get",
                  dataType:"json",
                  success:function(datas){
                    t.$set("current_page",(parseInt(t.current_page)-1));
                    t.$set("srvs",datas.results);
                  }
                })
            }
          },
          loadnextsrv:function(){
            var t = this;
            var fuhao = t.currentsrvurl.indexOf("?")>-1?"&":"?";
            if(t.current_page==t.pages){
              return false;
            }else{
                $.ajax({
                  url:t.currentsrvurl+fuhao+"page_size="+t.page_size+"&page="+(parseInt(t.current_page)+1),
                  type:"get",
                  dataType:"json",
                  success:function(datas){
                    t.$set("current_page",(parseInt(t.current_page)+1));
                    t.$set("srvs",datas.results);
                  }
                })
            }
          },
          deleteregion:function(id){
            var that = this;
            if(confirm("您确定要删除此标签吗？")){
              $.ajax({
                url:"api/"+appid+"/region/"+id+"/delete",
                type:"delete",
                dataType:"json",
                success:function(datas){
                  if(!datas){
                    toastr.success("删除成功","成功");
                  }
                  if(datas){
                    !datas.success?toastr.error(datas.msg,"失败"):toastr.success("删除成功","成功");
                  }
                  $.ajax({
                    url:"/api/"+appid+"/"+that.platidfortab+"/regions/",
                    type:"get",
                    dataType:"json",
                    success:function(datas){
                      var arr = [{key:"__all__",value:"所有区服"}];
                      for(var i=0;i<datas.results.length;i++){
                        arr.push({
                          key:datas.results[i].region_uuid,
                          value:datas.results[i].name,
                          url:datas.results[i].url
                        })
                      }
                      that.$set("tabs",arr);
                    }
                  })
                }
              })
            }
          },
          /*srv init cmd*/
          initcmd:function(event,cmdid,type){
            function ihdm(val){
              var it = "";
              var line = val.indexOf("-")>0?'-':'/';
              var time = val.split(" ")[1];
              var i = time.split(":")[1],h = time.split(":")[0];
              var date = val.split(" ")[0];
              var d = date.split(line)[2],m = date.split(line)[1];
              return [i,h,d,m];
            }
            var t = this;
            var url = type=="host"?this.selecthosturl:this.selectSrvurl;
            var selected = type=="host"?this.selectedhost :this.selectSrv;
            // console.log(url)
            url = type=="host"?url.replace("hosts","execute"):url.replace("zones","execute");
            var arr = [],obj = {};
            for(var i =0;i<selected.length;i++){
              type=="host"?arr.push(selected[i]):arr.push(selected[i].uuid);
            }
            $(event.target).parents("form").find(".envs").each(function(){
              if($(this).find("input.key").val()){
                obj[$(this).find("input.key").val()] = $(this).find("input.value").val();
              }
            })
            var data = {
              "workflow_uuid": cmdid,
               "uuids": type=="host"?arr.join(","):(t.ifall?"__all__":arr.join(",")),
               "region":t.currentregion,
               "kind":type,
               "timeout": $(event.target).parents("form").find("input[name='timeout']").val(),
               "inject_env": obj,
            }
            if(t.istimeout){
              data["name"] = $(event.target).parents("form").find("input[name='name']").val();
              data["cronExpression"] = ihdm($(event.target).parents("form").find("#timecron").val()).join(",");
            }
            // console.log(data)
            $.ajax({
              url:url,
              type:"post",
              dataType:"json",
              contentType:"application/json",
              data:JSON.stringify(data),
              success:function(datas){
                // console.log(datas)
                t.selectSrv = [];
                t.closeplat(event,cmdid);
                if(datas){
                    !datas.success?toastr.error(datas.msg,"失败"):toastr.success(datas.msg,"成功");
                }
              }
            })
          },
          addenvs:function(){
            this.envs+=1;
          },
          minusenvs:function(){
            this.envs-=1;
          },
          changetimeout:function(it,index){
            var _this = this;
            this.istimeout = it;
            this.$nextTick(function(){
              if(it){
                if($("#"+_this.common+"_"+index+"_manage").find("#timecron").length>0){
                  $("#"+_this.common+"_"+index+"_manage").find("#timecron").datetimepicker({
                    formatTime:'H:i',
                      formatDate:'Y-m-d',
                      timepickerScrollbar:false
                      ,step:5,
                      lang:'ch'});
                }
              }
            })

          },
          /*log detail*/
          getLogTwo:function(url){
            var _this = this;
            if(!$("#logdetail-two").hasClass('active')){
              $("#logdetail-two").addClass("active");
            }
            $(id).find("#loglog").html("");
            function operateFormatter(value, row, index){
              var ele = [
                '<a class="logdetailthree" data-url="'+row.url+'">'+row.remote_ip+'</a>'
              ]
              return ele.join('');
            }
            var logthreeEvent = {
              'click .logdetailthree':function(e, value, row, index){
                $.ajax({
                  url:row.url,
                  type:"get",
                  dataType:"json",
                  success:function(loglog){
                    var stderr = "";
                    var stdout = "";
                    if(loglog.stderr){
                        stderr = '<pre style="background-color:#ffffff;border:none">' + loglog.stderr + '</pre>';
                    }
                    if(loglog.stdout){
                        stdout = '<pre style="background-color:#ffffff;border:none">' + loglog.stdout + '</pre>';
                    }
                    $(id).find("#loglog").html([
                      '<div class="bs-callout bs-callout-danger"><h4>错误输出:</h4>' + stderr+ '</div>',
                      '<div class="bs-callout bs-callout-info"><h4>标准输出:</h4>' + stdout + '</div>',
                      ].join(''));
                    //$(id).find("#loglog").find("code").each(function(i, block) {
                    //  hljs.highlightBlock(block);
                    //});
                  }
                })
              }
            }
            $.ajax({
              url:url,
              type:"get",
              dataType:"json",
              success:function(data){
                // console.log(data.results);
                var detail2 = $(id).find("#log_two_table");
                detail2.bootstrapTable({
                  data:data.results,
                  columns:[
                    {
                        field: 'remote_ip',
                        title: '服务器IP',
                        sortable: true,
                        searchable:true,
                        events: logthreeEvent,
                        formatter: operateFormatter,
                        align: 'center'
                    }, {
                        field: 'sid',
                        title: '区服ID',
                        searchable:true,
                        sortable: true,
                        // footerFormatter: totalNameFormatter,
                        align: 'center'
                    },{
                        field: 'rc',
                        title: '返回状态码',
                        searchable:true,
                        sortable: true,
                        // footerFormatter: totalNameFormatter,
                        align: 'center'
                    },{
                        field: 'elapsed',
                        title: '总耗时(秒)',
                        searchable:true,
                        sortable: true,
                        // footerFormatter: totalNameFormatter,
                        align: 'center'
                    }
                  ]
                });
                detail2.bootstrapTable('load',data.results);
              }
            })
          },

          removescs:function(type){
            var _t = this;
            var url = {
              "script":"/api/"+appid+"/scripts/"+_t.selecteddel[type][0]+"/delete",
              "wkf":"/api/"+appid+"/workflows/"+_t.selecteddel[type][0]+"/delete",
              "approle":"/api/"+appid+"/roles/"+_t.selecteddel[type][0]+"/delete"
            }
            $.ajax({
              url:url[type],
              type:"delete",
              dataType:"json",
              success:function(datas){
                if(type!="script"){
                  if(datas.success){
                    toastr.success(datas.msg,datas.success?"成功":"失败");
                  }else{
                    toastr.error(datas.msg,datas.success?"成功":"失败");
                  }
                }else{
                  toastr.success("删除成功","成功");
                }
                
              }
            })
          },

          /*以下是关于tab内弹窗*/
          showp:function(event,index,callback){
              var _this = this;
              if(this.platzooms[index]){
                var _this = this;
                $("#desktop").find("li[data-target='"+_this.common+"_"+index+"_manage']").addClass('flop').one(transitionEnd,function(){
                    $(this).removeClass('flop');
                    desks.toggleMin(event,index+"_manage",true);
                });
                return false;
              }
              

              this.platzooms[index] = true;
              zindex++;
              $("#"+_this.common+"_"+index+"_manage").addClass('in');
              $("#"+_this.common+"_"+index+"_manage").css("z-index",zindex);
              $("#"+_this.common+"_"+index+"_manage").find(".modal-dialog").css("z-index",1050+zindex);
              GCR.modals.show($("#"+_this.common+"_"+index+"_manage"));

              if(_this.platcreateurls[index]){
                $.ajax({
                    url:_this.platcreateurls[index],
                    type:"get",
                    async:false,
                    dataType:"html",
                    success:function(html){
                       $("#"+_this.common+"_"+index+"_manage").find(".modal-body").html(html);
                       var tbcdf = new tabchildfunc();
                       if(index=="addworkflow"){
                        tbcdf.workflowadd();
                       }
                    }
                });
              }
              callback&&callback();
          },
          closeplat:function(event,index,p){
            var _this = this;
            event.stopPropagation();
            !p?this.platzooms[index] = false:null;
            !p?zindex--:null;
            $("#"+_this.common+"_"+index+"_manage").find(".modal-dialog").css("z-index","");
            $("#"+_this.common+"_"+index+"_manage").removeClass('maxmodal');
            if(p){
              $("#"+_this.common+"_"+index+"_manage").removeClass('slideInUp').addClass("zoomOutDown").one(transitionEnd,function(){
                if($(this).hasClass("zoomOutDown")){
                  $(this).removeClass('in');
                }
              });
            }else{
              $("#"+_this.common+"_"+index+"_manage").removeClass('in');
            }
          },
          minplat:function(event,index){
            var _this = this;
            event.stopPropagation();
            this.closeplat(event,index,"animate");//与关闭操作相同，并加入到desktop最小化列表中
            var name = $("#"+_this.common+"_"+index+"_manage").find(".modal-title").text();
            var icon = 'static/images/desktop-icons/folder-document.png';
            desks.minifys.push({
              el:$("#"+_this.common+"_"+index+"_manage"),
              target:_this.common+"_"+index+"_manage",
              index:index,
              // show:false,
              name:name,
              icon:icon,
            });
            desks.isflop.push(false);
            GCR.fishdock();
            GCR.modals.min(this.target[index]);
          },
          maxplat:function(event,index){
              this.platismax[index] = !this.platismax[index];
              var _target = this.target[index];
              if(this.platismax[index]){//经过上述转换以后说明platismax是放大时候的状态，因此，要记录原始的width height left top等
                this.platinit_val[index] = {
                  left:_target.offsetLeft,
                  top:_target.offsetTop,
                  width:_target.offsetWidth,
                  height:_target.offsetHeight
                }
              }
              GCR.modals.max(this.platismax[index],this.target[index],this.platinit_val[index]);
          },
        }
      });
      // localStorage.setItem()

      var tf = new tabFunc();
      tf.dashboardinit(id,appid);
      tf.hostinit(id,appid);
      tf.srvinit(id,appid);
      tf.cmdinit(id,appid);
      tf.timeworkflow(id,appid);
      tf.workflowinit(id,appid);
      tf.loginit(id,appid);
      tf.platinit(id,appid);
      tf.roleinit(id,appid);

      var list = [
        '',
        '',
        'loadcmd',
        '',
        '',
        '',
        'tf.loginit(id,appid)',
        '',
        ''
      ];
      $(id).find("ul.nav li").click(function(){
        var t = $(this);
        if(list[t.index()]=="loadcmd"){
          var cmdurl = $(id).find("input[data-type='workflow']").val();
          $.ajax({
            url:cmdurl+"?page_size=100&page=1",
            type:"get",
            dataType:"json",
            success:function(data){
              tabss[id].$set("hostcmds",data.results);
              var srvcmds = data.results;
              // console.log(srvcmds)
              tabss[id].$nextTick(function () {
                for(var c = 0;c<srvcmds.length;c++){
                    tabss[id].$set("platzooms['host_"+srvcmds[c].uuid+"']",false);
                    tabss[id].$set("platismax['host_"+srvcmds[c].uuid+"']",false);
                    // console.log(app)
                    $(id+"_host_"+srvcmds[c].uuid+"_manage").appendTo($("body"));
                    tabss[id].$set("target['host_"+srvcmds[c].uuid+"']",$(id+"_host_"+srvcmds[c].uuid+"_manage").find(".modal-dialog"));
                    $(id+"_host_"+srvcmds[c].uuid+"_manage").find(".modal-dialog").addClass("dialog-init").wsresizable();
                    $(id+"_host_"+srvcmds[c].uuid+"_manage").wsdraggable({handle:'.modal-header'});
                    // $("#"+srvcmds[c].uuid+"_btn").click(function(e){
                    //   tabss[localStorage.getItem("currentapp")].showp(e,$(this).attr("id").split("_btn")[0]);
                    // })
                  }
              })
              
            }
          })
          return false;
        }
        list[t.index()]?eval("("+list[t.index()]+")"):null;
      })

      $(document).keyup(function(e){
         $(".modal").find("#srv-datas li").css({
             '-moz-user-select': '#39ADB4', 
             '-webkit-user-select': '#39ADB4',
             '-ms-user-select': '#39ADB4',
             '-khtml-user-select': '#39ADB4',
             'user-select': '#39ADB4',
        })
      });
      $(".customsrvtab").delegate("ul.nav-tabs li","click",function(){
        $(".customsrvtab ul.nav-tabs li").removeClass('active');
        var t = $(this);
        t.addClass('active');
        // t.parents(".customtab").find(".tab-content").find(".tab-pane").removeClass('active');
        // t.parents(".customtab").find(".tab-content").find(t.attr("data-target")).addClass('active');
      })

  }
  function tabFunc(){};
  
  /**
  *加载概览页tab
  **/

  tabFunc.prototype.dashboardinit = function(id,appid){

    var type="dashboard";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();
    // $(app).find("#dashboard").attr("src",url);

    $.ajax({
      url:"/api/"+appid+"/widgets",
      type:"get",
      dataType:"json",
      success:function(data){
        tabss[app].$set("widget",data.results);
      }
    })
    $.ajax({
      url:"/api/users/"+appid+"/widgets",
      type:"get",
      dataType:"json",
      success:function(data){
        tabss[app].$set("widgetSelected",data.results);
        var yuzhi = data.results;
        var block = [],pie=[],line=[],column=[];
        for(var i =0;i<yuzhi.length;i++){
          $.ajax({
            url:yuzhi[i].url,
            type:"get",
            dataType:"json",
            success:function(data){
              if(data.kind == "block"){
                block.push(data);
              }
              if(data.kind == "pie"){
                pie.push(data);
              }
              if(data.kind == "line"){
                line.push(data);
              }
              if(data.kind == "column"){
                column.push(data);
              }
            }
          })
        }

        tabss[app].$set("block",block);
        tabss[app].$set("pie",pie);
        tabss[app].$set("line",line);
        tabss[app].$set("column",column);
        tabss[app].$watch("pie",function(pie){
            for(var i=0;i<pie.length;i++){
              $("#"+tabss[app].common+"_"+pie[i].kind+"_charts"+i).highcharts({
                  chart: {
                      plotBackgroundColor: null,
                      plotBorderWidth: null,
                      plotShadow: false
                  },
                  credits: {
                      text: '',
                      href: ''
                  },
                  title: {
                      text:""
                  },
                  tooltip: {
                    pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
                  },
                  plotOptions: {
                      pie: {
                          allowPointSelect: true,
                          cursor: 'pointer',
                          dataLabels: {
                              enabled: true,
                              color: '#000000',
                              connectorColor: '#000000',
                              format: ''
                          }
                      }
                  },
                  series: [{
                      type: 'pie',
                      name: '',
                      data: pie[i].series
                  }]
              });
            }
        });
        var id = localStorage.getItem("currentappid")
        // console.log(id)
        $("#addchart form input[type='button']").unbind("click").click(function(){
          // console.log("aasdfasdf")
          var form = $(this).parents("form");
          $.ajax({
            url:"api/users/widgets/create",
            type:"post",
            dataType:"json",
            data:{
              widget_id:form.find("select").val(),
              appid:id
            },
            success:function(data){
              if(data.success){
                tabss[app].$set("addchart",false);
                locacmdbdashboard(url);
              }
            }
          })
        })//users/widgets/create/
      }
    })
  }

  /**
  *加载服务器tab
  **/
  tabFunc.prototype.hostinit = function(id,appid){
    var type = "host";
    var app = id;
    // console.log(app)
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();
    $(app).find("#tree").bind("mousedown",function (event){
      if(event.which==3){
         $("#treeright").css("top",event.pageY-20).css("left",event.pageX).css({"position":"fixed","z-index":"9999"}).addClass("open");
      }
      if(event.which ==1){
        $("#treeright").removeClass("open");
      }
      treeright.$set("currenttree",$(app).find("#tree"));
      treeright.$set("appid",appid);
      treeright.$set("treeurl",url);
    });
    refreshtree();
    function refreshtree(param){
        if(param){
          $(app).find("#tree").fancytree({url:url});
          return false;
        }
        $(app).find("#tree").fancytree({
            source:{url:url},
            extensions: ["dnd"],
            dnd: {
                  preventVoidMoves: true, // Prevent dropping nodes 'before self', etc.
                  preventRecursiveMoves: true, // Prevent dropping nodes on own descendants
                  autoExpandMS: 400,
                  refreshPositions: true,
                  draggable: {
                    appendTo: "body",  // We don't want to clip the helper inside container
                    // scroll: false,
                    // containment: "parent",  // $("ul.fancytree-container"),
                    // cursorAt: { left: 5 },
                    revert: "invalid"
                    // revert: function(dropped) {
                    //   return
                    // }
                  },
                  dragStart: function(node, data) {
                    // allow dragging `node`:
                    return true;
                  },
                  dragEnter: function(node, data) {
                     return true;
                  },
                  initHelper: function(node, data) {
                    // Helper was just created: modify markup
                    var helper = data.ui.helper,
                      sourceNodes = data.tree.getSelectedNodes();

                    // Store a list of active + all selected nodes
                    if( !node.isSelected() ) {
                      sourceNodes.unshift(node);
                    }
                    helper.data("sourceNodes", sourceNodes);
                    // Mark selected nodes also as drag source (active node is already)
                    $(".fancytree-active,.fancytree-selected", tree.$container)
                      .addClass("fancytree-drag-source");
                    // Add a counter badge to helper if dragging more than one node
                    if( sourceNodes.length > 1 ) {
                      helper.append($("<span class='fancytree-childcounter'/>")
                        .text("+" + (sourceNodes.length - 1)));
                    }
                    // Prepare an indicator for copy-mode
                    helper.prepend($("<span class='fancytree-dnd-modifier'/>")
                      .text("+").hide());
                  },
                  updateHelper: function(node, data) {
                    // Mouse was moved or key pressed: update helper according to modifiers

                    // NOTE: pressing modifier keys stops dragging in jQueryUI 1.11
                    // http://bugs.jqueryui.com/ticket/14461
                    var event = data.originalEvent,
                      tree = node.tree,
                      copyMode = event.ctrlKey || event.altKey;

                    // Adjust the drop marker icon
                    //          data.dropMarker.toggleClass("fancytree-drop-copy", copyMode);

                    // Show/hide the helper's copy indicator (+)
                    data.ui.helper.find(".fancytree-dnd-modifier").toggle(copyMode);
                    // tree.debug("1", $(".fancytree-active,.fancytree-selected", tree.$container).length)
                    // tree.debug("2", $(".fancytree-active,.fancytree-selected").length)
                    // Dim the source node(s) in move-mode
                    $(".fancytree-drag-source", tree.$container)
                      .toggleClass("fancytree-drag-remove", !copyMode);
                    // data.dropMarker.toggleClass("fancytree-drop-move", !copyMode);
                  },
                  dragDrop: function(node, data) {
                    var sourceNodes = data.ui.helper.data("sourceNodes"),
                      event = data.originalEvent,
                      copyMode = event.ctrlKey || event.altKey;

                    if( copyMode ) {
                      $.each(sourceNodes, function(i, o){
                        o.copyTo(node, data.hitMode, function(n){
                          delete n.key;
                          n.selected = false;
                          n.title = "Copy of " + n.title;
                        });
                      });
                    }else{
                      $.each(sourceNodes, function(i, o){
                        o.moveTo(node, data.hitMode);
                      });
                    }
                  }
            },
            renderNode:function(event,data){
              var node = data.node;
              if(node.children){
                $(node.li).css("position","relative").append('<i @click="show('+event+',\'updatepgroup\')" class="edit glyphicon glyphicon-edit"></i><i class="remove glyphicon glyphicon-trash"></i>');
              }
            },
            focus: function(event, data) {
              var node = data.node;
              // Auto-activate focused node after 1 second
              if(node.data.url){
                node.scheduleAction("activate", 1000);
              }
            },
            blur: function(event, data) {
              data.node.scheduleAction("cancel");
            },
            activate: function(event, data){
              var node = data.node,
                orgEvent = data.originalEvent || {};
              if(node.data.url){
                // $.ajax({
                //  url:node.data.url,
                //  type:"get",
                //  dataType:"json",
                //  success:function(data){
                    loadhost($(app).find("#hosttable"),node.data.url);
                  // }
                // })
              }
              //在这里执行ajax方法
              // if(node.data.href){
              //  window.open(node.data.href, (orgEvent.ctrlKey || orgEvent.metaKey) ? "_blank" : node.data.target);
              // }
              // if( window.parent &&  parent.history && parent.history.pushState ) {
              //  // Add #HREF to URL without actually loading content
              //  parent.history.pushState({title: node.title}, "", "#" + (node.data.href || ""));
              // }
            },
            click: function(event, data){ // allow re-loads
              // console.log("点击")
              var node = data.node,
                orgEvent = data.originalEvent;
              if(data.originalEvent.target.tagName=="I"){
                treeright.$set("groupid",node.key);
                if(data.originalEvent.target.className.indexOf("edit")>-1){
                  console.log("编辑")
                  treeright.show(event,'updatepgroup');
                }else if(data.originalEvent.target.className.indexOf("remove")>-1){
                  console.log("删除")
                  if(confirm("您确定要删除此平台组吗？")){
                    $.ajax({
                      url:"/api/platgroup/"+node.key+"/delete",
                      type:"delete",
                      dataType:"json",
                      success:function(datas){
                        if(!datas){
                          toastr.success("删除成功","成功");
                        }
                        if(datas){
                          !datas.success?toastr.error(datas.msg,"失败"):toastr.success("删除成功","成功");
                        }
                        refreshtree(1);
                      }
                    })
                  }
                }
              }else{
                if(data.originalEvent.target.className.indexOf("fancytree-expander")==-1){
                  if(node.data.url){
                    $(app).find("#hosttable").bootstrapTable('destroy');
                    loadhost($(app).find("#hosttable"),node.data.url);
                    tabss[app].$set("selecthosturl",node.data.url);
                    // data.tree.reactivate();
                    // window.open(node.data.href, (orgEvent.ctrlKey || orgEvent.metaKey) ? "_blank" : node.data.target);
                  }
                }
                
              }
              
            },
            done:function(){
              alert("111")
            }   
        })
            

    }

    $("#refreshthistree").click(function(){
      refreshtree(1);
    })
    var cmdurl = $(app).find("input[data-type='workflow']").val();
    $.ajax({
      url:cmdurl+"?page_size=100&page=1",
      type:"get",
      dataType:"json",
      success:function(data){
        tabss[app].$set("hostcmds",data.results);
        var srvcmds = data.results;
        // console.log(srvcmds)
        tabss[app].$nextTick(function () {
          for(var c = 0;c<srvcmds.length;c++){
              tabss[app].$set("platzooms['host_"+srvcmds[c].uuid+"']",false);
              tabss[app].$set("platismax['host_"+srvcmds[c].uuid+"']",false);
              // console.log(app)
              $(app+"_host_"+srvcmds[c].uuid+"_manage").appendTo($("body"));
              tabss[app].$set("target['host_"+srvcmds[c].uuid+"']",$(app+"_host_"+srvcmds[c].uuid+"_manage").find(".modal-dialog"));
              $(app+"_host_"+srvcmds[c].uuid+"_manage").find(".modal-dialog").addClass("dialog-init").wsresizable();
              $(app+"_host_"+srvcmds[c].uuid+"_manage").wsdraggable({handle:'.modal-header'});
              // $("#"+srvcmds[c].uuid+"_btn").click(function(e){
              //   tabss[localStorage.getItem("currentapp")].showp(e,$(this).attr("id").split("_btn")[0]);
              // })
            }
        })
        
      }
    })
    // console.log(tab.parent().find(".wstree"))
    // tab.parent().find(".wstree").css("height",$(app).find(".modal-dialog")[0].offsetHeight-tab.parent()[0].offsetTop);
    function loadhost(it,url){
      // console.log(it)
      it.bootstrapTable({
        height:getHeight(it),
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        // dataField:'rows',
        // maintainSelected:true,//在更改和搜索时保持选定的行
        // searchOnEnterKey:"true",
        columns: [
          {
              field: 'state',
              checkbox: true,
              align: 'center',
              valign: 'middle'
          }, {
              field: 'public_ip',
              title: '服务器IP',
              searchable:true,
              sortable: true,
              formatter: replacepro,
              align: 'center'
          },
          {
              field: 'cpu_core',
              title: 'CPU核数',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }, {
              field: 'memory_capacity',
              title: '内存',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }, {
              field: 'disk_capacity',
              title: '硬盘大小',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }, {
              field: 'source',
              title: '来源',
              sortable: true,
              searchable:true,
              align: 'center'
          }, {
              field: 'states',
              title: '状态',
              sortable: true,
              align: 'center',
          },{
              field: 'expire',
              title: '是否在保',
              sortable: true,
              align: 'center',
              formatter: platsiteformatter,
          },{
            field:'zones',
            title:'区服',
            sortable:true,
            align:'center',
            formatter:zoneformatter
          }
        ],
      });
      // setTimeout(function () {
      //     $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
      //       var that = $(this);
      //       that.parent().toggleClass('open');
      //       $(document).mousedown(function(event){
      //         if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
      //           that.parent().removeClass('open');
      //         }
      //       })
      //     });
      // }, 200);
      // sometimes footer render error.
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
        // console.log(selections)
        tabss[app].$set("selectedhost",selections);
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
      $("#apphostsearch").unbind("keyup").keyup(function(e){
        var val = $(this).val();
        if(val==""){
          it.bootstrapTable("refresh",{url:url});
        }
        if(e.keyCode==13){
          it.bootstrapTable("refresh",{url:"/api/"+appid+"/search/hosts?search="+val});
        }
      })
    }
    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it[0].offsetTop - 110;
    }
    function platsiteformatter(value,row,index){
      return value?'<i class="glyphicon glyphicon-remove" style="color:red"></i>':'<i style="color:#39adb4" class="glyphicon glyphicon-ok"></i>';
    }
    function replacepro(value,row,index){
      return value+'<input type="hidden" name="uuid" value="'+row.uuid+'">';
    }
    function zoneformatter(value,row,index){
      var arr = [];
      for(var i=0;i<value.length;i++){
        arr.push(value[i].alias);
      }
      arr.sort();
      return arr.join(",");
    }
  }
  /**
  *加载区服tab
  **/
  tabFunc.prototype.srvinit = function(id,appid){
    var type="srv";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();
    $(app).find("#srvtree").bind("mousedown",function (event){
      if(event.which==3){
         $("#treeright").css("top",event.pageY-20).css("left",event.pageX).css({"position":"fixed","z-index":"9999"}).addClass("open");
      }
      if(event.which ==1){
        $("#treeright").removeClass("open");
      }
      treeright.$set("currenttree",$(app).find("#srvtree"));
      treeright.$set("appid",appid);
      treeright.$set("treeurl",url);
    });
    refreshtree();
    function refreshtree(param){
      if(param){
        $(app).find("#srvtree").fancytree({url:url});
        return false;
      }
      $(app).find("#srvtree").fancytree({
          source:{url:url},
          extensions: ["dnd"],
          dnd: {
                preventVoidMoves: true, // Prevent dropping nodes 'before self', etc.
                preventRecursiveMoves: true, // Prevent dropping nodes on own descendants
                autoExpandMS: 400,
                refreshPositions: true,
                draggable: {
                  appendTo: "body",  // We don't want to clip the helper inside container
                  // scroll: false,
                  // containment: "parent",  // $("ul.fancytree-container"),
                  // cursorAt: { left: 5 },
                  revert: "invalid"
                  // revert: function(dropped) {
                  //   return
                  // }
                },
                dragStart: function(node, data) {
                  // allow dragging `node`:
                  return true;
                },
                dragEnter: function(node, data) {
                   return true;
                },
                initHelper: function(node, data) {
                  // Helper was just created: modify markup
                  var helper = data.ui.helper,
                    sourceNodes = data.tree.getSelectedNodes();

                  // Store a list of active + all selected nodes
                  if( !node.isSelected() ) {
                    sourceNodes.unshift(node);
                  }
                  helper.data("sourceNodes", sourceNodes);
                  // Mark selected nodes also as drag source (active node is already)
                  $(".fancytree-active,.fancytree-selected", tree.$container)
                    .addClass("fancytree-drag-source");
                  // Add a counter badge to helper if dragging more than one node
                  if( sourceNodes.length > 1 ) {
                    helper.append($("<span class='fancytree-childcounter'/>")
                      .text("+" + (sourceNodes.length - 1)));
                  }
                  // Prepare an indicator for copy-mode
                  helper.prepend($("<span class='fancytree-dnd-modifier'/>")
                    .text("+").hide());
                },
                updateHelper: function(node, data) {
                  // Mouse was moved or key pressed: update helper according to modifiers

                  // NOTE: pressing modifier keys stops dragging in jQueryUI 1.11
                  // http://bugs.jqueryui.com/ticket/14461
                  var event = data.originalEvent,
                    tree = node.tree,
                    copyMode = event.ctrlKey || event.altKey;

                  // Adjust the drop marker icon
              //          data.dropMarker.toggleClass("fancytree-drop-copy", copyMode);

                  // Show/hide the helper's copy indicator (+)
                  data.ui.helper.find(".fancytree-dnd-modifier").toggle(copyMode);
                  // tree.debug("1", $(".fancytree-active,.fancytree-selected", tree.$container).length)
                  // tree.debug("2", $(".fancytree-active,.fancytree-selected").length)
                  // Dim the source node(s) in move-mode
                  $(".fancytree-drag-source", tree.$container)
                    .toggleClass("fancytree-drag-remove", !copyMode);
                  // data.dropMarker.toggleClass("fancytree-drop-move", !copyMode);
                },
                dragDrop: function(node, data) {
                  var sourceNodes = data.ui.helper.data("sourceNodes"),
                    event = data.originalEvent,
                    copyMode = event.ctrlKey || event.altKey;

                  if( copyMode ) {
                    $.each(sourceNodes, function(i, o){
                      o.copyTo(node, data.hitMode, function(n){
                        delete n.key;
                        n.selected = false;
                        n.title = "Copy of " + n.title;
                      });
                    });
                  }else{
                    $.each(sourceNodes, function(i, o){
                      o.moveTo(node, data.hitMode);
                    });
                  }
                }
          },
          renderNode:function(event,data){
            var node = data.node;
            if(node.children){
              $(node.li).css("position","relative").append('<i @click="show('+event+',\'updatepgroup\')" class="edit glyphicon glyphicon-edit"></i><i class="remove glyphicon glyphicon-trash"></i>');
            }
          },
          focus: function(event, data) {
            var node = data.node;
            // Auto-activate focused node after 1 second
            if(node.data.url){
              node.scheduleAction("activate", 1000);
            }
          },
          blur: function(event, data) {
            data.node.scheduleAction("cancel");
          },
          activate: function(event, data){
            var node = data.node,
              orgEvent = data.originalEvent || {};
            if(node.data.url){
              // $.ajax({
              //   url:node.data.url,
              //   type:"get",
              //   dataType:"json",
              //   success:function(jon){
              //     tabss[app].$set("srvs",jon.results);
                  
              //   }
              // })
                }
          },
          click: function(event, data){ // allow re-loads
            var node = data.node,
              orgEvent = data.originalEvent;
              console.log(event)
              if(data.originalEvent.target.tagName=="I"){
                treeright.$set("groupid",node.key);
                if(data.originalEvent.target.className.indexOf("edit")>-1){
                  console.log("编辑")
                  treeright.show(event,'updatepgroup');
                }else if(data.originalEvent.target.className.indexOf("remove")>-1){
                  console.log("删除")
                  if(confirm("您确定要删除此平台组吗？")){
                    $.ajax({
                      url:"/api/platgroup/"+node.key+"/delete",
                      type:"delete",
                      dataType:"json",
                      success:function(datas){
                        if(!datas){
                          toastr.success("删除成功","成功");
                        }
                        if(datas){
                          !datas.success?toastr.error(datas.msg,"失败"):toastr.success("删除成功","成功");
                        }
                        refreshtree(1);
                      }
                    })
                  }
                }
              }else{
                if(orgEvent.target.className.indexOf("fancytree-expander")==-1){
                  if(node.data.url){
                    if(window.sendSrv)clearTimeout(window.sendSrv);
                    tabss[app].$set("loadsrvurl",node.data.url);
                    tabss[app].$set("platidfortab",node.key);
                    tabss[app].$set("platcreateurls.createregion","/ops/"+appid+"/region/create");
                    $.ajax({
                      url:"/api/"+appid+"/"+node.key+"/regions/",
                      type:"get",
                      dataType:"json",
                      success:function(datas){
                        var arr = [{key:"__all__",value:"所有区服"}];
                        for(var i=0;i<datas.results.length;i++){
                          arr.push({
                            key:datas.results[i].region_uuid,
                            value:datas.results[i].name,
                            url:datas.results[i].url
                          })
                        }
                        tabss[app].$set("tabs",arr);
                      }
                    })


                    $(".loading").show();
                    tabss[app].$set("currentsrvurl",node.data.url)
                    $.ajax({
                      url:node.data.url+"?page_size="+tabss[app].page_size+"&page=1",
                      type:"get",
                      dataType:"json",
                      success:function(jon){
                        tabss[app].$set("srvs",jon.results);
                        tabss[app].$set("pages",Math.ceil(jon.count/parseInt(tabss[app].$get("page_size"))));
                        tabss[app].$set("selectSrvurl",node.data.url);
                        $(".loading").hide();
                        var ips = [];
                        for(var i=0;i<jon.results.length;i++){
                          ips.push(jon.results[i].server.remote_ip);
                        }
                        ips = ips.unique();
                        function SocketSrv(data){
                          soc.ws.send(data);
                          window.sendSrv = setTimeout(function(){
                            SocketSrv(data);
                          },5000)
                        }

                        SocketSrv(JSON.stringify(ips));
                        
                        // soc.emit(JSON.stringify(ips));
                      }
                    })
                    // data.tree.reactivate();
                    // window.open(node.data.href, (orgEvent.ctrlKey || orgEvent.metaKey) ? "_blank" : node.data.target);
                  }
                }
              }
          },
          done:function(){
            alert("222")
          }  
      });
    }

    $("#refreshthistree").click(function(){
      refreshtree(1);
    })    

    var cmdurl = $(app).find("input[data-type='workflow']").val();
    $.ajax({
      url:cmdurl+"?page_size=100&page=1",
      type:"get",
      dataType:"json",
      success:function(data){
        tabss[localStorage.getItem("currentapp")].$set("srvcmds",data.results);
        var srvcmds = data.results;
        // console.log(srvcmds)
        tabss[localStorage.getItem("currentapp")].$nextTick(function () {
          for(var c = 0;c<srvcmds.length;c++){
              tabss[localStorage.getItem("currentapp")].$set("platzooms['"+srvcmds[c].uuid+"']",false);
              tabss[localStorage.getItem("currentapp")].$set("platismax['"+srvcmds[c].uuid+"']",false);
              // console.log(app)
              $(app+"_"+srvcmds[c].uuid+"_manage").appendTo($("body"));
              tabss[localStorage.getItem("currentapp")].$set("target['"+srvcmds[c].uuid+"']",$(app+"_"+srvcmds[c].uuid+"_manage").find(".modal-dialog"));
              $(app+"_"+srvcmds[c].uuid+"_manage").find(".modal-dialog").addClass("dialog-init").wsresizable();
              $(app+"_"+srvcmds[c].uuid+"_manage").wsdraggable({handle:'.modal-header'});
              // $("#"+srvcmds[c].uuid+"_btn").click(function(e){
              //   tabss[localStorage.getItem("currentapp")].showp(e,$(this).attr("id").split("_btn")[0]);
              // })
            }
        })
        
      }
    })
    // tab.parent().find(".wstree").css("height",$(app).find(".modal-dialog")[0].offsetHeight-tab.parent()[0].offsetTop);
  }
  /**
  *加载脚本tab
  **/
  tabFunc.prototype.cmdinit = function(id,appid){
    // console.log("incmd")
    var type = "script";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();

    var it = $(app).find("#cmd_table");
    // loadcmd(it,url)

    var getupdatecmd = {
      'click .btn':function(e, value, row, index){
        // console.log(e.target.id.split("_")[1])
        tabss[app].$set("platcreateurls.updatecmd",row.url);
        tabss[app].showp(e,e.target.id.split("_")[1]);
      }
    }

    // function loadcmd(it,url){
      it.bootstrapTable({
        // height:getHeight(it),
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        // dataField:'rows',
        // maintainSelected:true,//在更改和搜索时保持选定的行
        // searchOnEnterKey:"true",
        columns: [
          {
              field: 'state',
              checkbox: true,
              align: 'center',
              valign: 'middle'
          },{
              field: 'name',
              title: '脚本名称',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }, {
              field: 'mode',
              title: '类型',
              searchable:true,
              sortable: true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          },{
              field: 'param',
              title: '参数',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          },{
              field: 'create_user',
              title: '创建人',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
            field:'operate',
            title:'操作',
            events:getupdatecmd,
            formatter:updatecmdfomatter,
            align:'center'
          }
        ],
      });
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
        tabss[app].$set("selecteddel.script",selections);
        if(selections.length==1){
          tabss[app].$set("deletebtn.script",true);
        }else{
          tabss[app].$set("deletebtn.script",true);
        }
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
    // }


    function updatecmdfomatter(value,row,index){
        var ele = $(modaltpl("updatecmd",["更新","更新命令"]));
        tabss[app].$compile(ele.get(0));
        ele.find(".modal-dialog").addClass("dialog-init").wsresizable();
        // console.log($(app).find(".modal").css("z-index"))
        ele.find(".modal-dialog").css("z-index",1050+5);
        ele.find(".modal").wsdraggable({handle:'.modal-header'});
        ele.find(".modal").appendTo($("body"));
        tabss[app].$set("target.updatecmd",ele.find(".modal-dialog"));

        return ele.find(".btn:first")[0].outerHTML;
    }
    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }


    var commonapp = localStorage.getItem("currentapp").split("#")[1];
    $("#"+commonapp).delegate("#"+commonapp+"_addcmd","click",function(e){
      tabss[localStorage.getItem("currentapp")].showp(e,'addcmd');
    })
  }
  /**
  *加载作业tab
  **/
  tabFunc.prototype.workflowinit = function(id,appid){
    var type = "workflow";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();

    var it = $(app).find("#workflow_table");

    var updatewf = {
      'click .btn':function(e, value, row, index){
        tabss[app].$set("platcreateurls.updateworkflow",row.url);
        tabss[app].showp(e,e.target.id.split("_")[1]);
      }
    }

    it.bootstrapTable({
      // height:getHeight(it),
      sidePagination:"server",
      url:url,
      queryParams:queryParams,
      responseHandler:responseHandler,
      // dataField:'rows',
      // maintainSelected:true,//在更改和搜索时保持选定的行
      // searchOnEnterKey:"true",
      columns: [
        {
            field: 'state',
            checkbox: true,
            align: 'center',
            valign: 'middle'
        },{
            field: 'name',
            title: '作业名称',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'mode',
            title: '类型',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        },{
            field: 'created_at',
            title: '创建时间',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        },{
            field: 'create_user',
            title: '创建人',
            sortable: true,
            searchable: true,
            align: 'center'
        },{
            field:'operate',
            title:'操作',
            align:'center',
            formatter:workflowupdate,
            events:updatewf
        }
      ],
    });
    it.on('check.bs.table uncheck.bs.table ' +
          'check-all.bs.table uncheck-all.bs.table', function () {
      selections = getIdSelections(it);
      tabss[app].$set("selecteddel.wkf",selections);
      if(selections.length==1){
        tabss[app].$set("deletebtn.wkf",true);
      }else{
        tabss[app].$set("deletebtn.wkf",true);
      }
    });
    it.on('all.bs.table', function (e, name, args) {
      
    });
     
    function workflowupdate(value,row,index){
      var ele = $(modaltpl("updateworkflow",["更新","更新工作流"]));
      tabss[app].$compile(ele.get(0));
      ele.find(".modal-dialog").addClass("dialog-init").wsresizable();
      // console.log($(app).find(".modal").css("z-index"))
      ele.find(".modal-dialog").css("z-index",1050+5);
      ele.find(".modal").wsdraggable({handle:'.modal-header'});
      ele.find(".modal").appendTo($("body"));
      tabss[app].$set("target.updateworkflow",ele.find(".modal-dialog"));

      return ele.find(".btn:first")[0].outerHTML;
    }  

    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }
        
    var commonapp = localStorage.getItem("currentapp").split("#")[1];
    $("#"+commonapp).delegate("#"+commonapp+"_addworkflow","click",function(e){
      tabss[localStorage.getItem("currentapp")].showp(e,'addworkflow');
    })
  }
  /**
  *加载定时任务
  **/
  tabFunc.prototype.timeworkflow = function(id,appid){
    var type = "cronjob";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();

    var it = $(app).find("#cronjob_table");

    var deletewf = {
      'click .delete_cron':function(e, value, row, index){
        // console.log(row);
        $.ajax({
          url:"api/"+row.app_uuid+"/cronjob/"+row.uuid+"/delete",
          type:"delete",
          dataType:"json",
          success:function(data){

          }
        })
      }
    }

    it.bootstrapTable({
      // height:getHeight(it),
      sidePagination:"server",
      url:url,
      queryParams:queryParams,
      responseHandler:responseHandler,
      // dataField:'rows',
      // maintainSelected:true,//在更改和搜索时保持选定的行
      // searchOnEnterKey:"true",
      columns: [
        {
            field: 'state',
            checkbox: true,
            align: 'center',
            valign: 'middle'
        },{
            field: 'name',
            title: '名称',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        },{
            field: 'appalias',
            title: '执行的应用',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'user',
            title: '创建人',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        },{
            field: 'crontab',
            title: '定时时间',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        },{
            field: 'created_at',
            title: '创建时间',
            sortable: true,
            searchable: true,
            align: 'center'
        },{
            field:'operate',
            title:'操作',
            align:'center',
            formatter:workflowupdate,
            events:deletewf
        }
      ],
    });
    it.on('check.bs.table uncheck.bs.table ' +
          'check-all.bs.table uncheck-all.bs.table', function () {
      selections = getIdSelections(it);
    });
    it.on('all.bs.table', function (e, name, args) {
      
    });
     
    function workflowupdate(value,row,index){
      var str = '<button class="delete_cron btn btn-danger">'+
        '<i class="glyphicon glyphicon-trash"></i>'+
       '</button>';
      return str;
    }  

    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }
        
    // var commonapp = localStorage.getItem("currentapp").split("#")[1];
    // $("#"+commonapp).delegate("#"+commonapp+"_addworkflow","click",function(e){
    //   tabss[localStorage.getItem("currentapp")].showp(e,'addworkflow');
    // })
  }
  /**
  *加载日志tab
  **/
  tabFunc.prototype.loginit = function(id,appid){
    var logchild = new Vue({
      el:"#logmanage",
      data:function(){
        return {
          // disabled:[],
          value:'',
          format:['yyyy-MM-dd'],
          reset:true,
        }
      },
    });
    var type = "log";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();
    // console.log(url)

    

    var logEvent = {
      'click .logdetail': function(e, value, row, index){
        if(!$(id+" #logdetail").hasClass('active')){
          // console.log("asdfasdf")
          $(id+" #logdetail").addClass("active");
          function getheight(it){
            return it.parents(".modal-body")[0].offsetHeight - it[0].offsetTop - 100;
          }
          var $table = $(app).find(".fixed-table-body table");
          if($table.length>0){
            $table.each(function(){
              var _that = $(this);
              if(!_that.attr("data-show-refresh"))return false;
              _that.bootstrapTable('resetView', {
                  height: getheight(_that)
              });
            })
          }
        }
        $.ajax({
          url:row.url,
          type:"get",
          dataType:"json",
          success:function(data){
            var dtai1 = data.results;
            // console.log(JSON.stringify(dtai1))
            // logwfs.$set("",dtai1);
            tabss[app].$set("steps",dtai1)
            // console.log(logwfs)
          }
        })
      },
    }
    $(id+" #logdetail .widget-icons").click(function(){
      $(id+" #logdetail").removeClass("active");
      $(id+" #logdetail-two").removeClass('active');
    })
    $(id+" #logdetail-two .widget-icons").click(function(){
      $(id+" #logdetail-two").removeClass('active');
    })
    var it = $(app).find("#log_table");
    loadlog(it,url)
    function loadlog(it,url){
      it.bootstrapTable({
        // height:getHeight(it),
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        // dataField:'rows',
        // maintainSelected:true,//在更改和搜索时保持选定的行
        // searchOnEnterKey:"true",
        columns: [
          {
              field: 'state',
              checkbox: true,
              align: 'center',
              valign: 'middle'
          },{
            field:'operate',
            title:'查看详情',
            align:'center',
            events: logEvent,
            formatter: operateFormatter
          },{
              field: 'app_alias',
              title: '执行应用',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }, {
              field: 'name',
              title: '任务名称',
              searchable:true,
              sortable: true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          },{
              field: 'triggers',
              title: '执行渠道',
              searchable:true,
              sortable: true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          },{
              field: 'user',
              title: '执行人',
              searchable:true,
              sortable: true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          },{
              field: 'progress',
              title: '状态',
              sortable: true,
              searchable:true,
              formatter: statusFormatter,
              align: 'center'
          },{
              field: 'start_at',
              title: '开始时间',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }
        ],
      });

      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
    }
    $(id+" #filterlog .btn").click(function(){
      var t = $(this);
      if(t.attr("data-type")!="all"){
        // console.log(url+"?status="+t.attr("data-type"))
        it.bootstrapTable("refresh",{url:url+"?status="+t.attr("data-type")});
      }else{
        it.bootstrapTable("refresh",{url:url});
      }
      $(id+" #filterlog .btn").removeClass('btn-primary').addClass('btn-default');
      t.addClass('btn-primary').removeClass('btn-default');
    })
    $(id+" #closetask").click(function(){
      $.ajax({
        url:"/api/"+appid+"/tasks/close/",
        type:"post",
        dataType:"json",
        data:{"uuids":selections.join(",")},
        success:function(datas){
          if(datas.success){
            toastr.success(datas.msg,"成功");
          }else{
            toastr.error(datas.msg,"失败");
          }
        }
      })
    });
    function statusFormatter(value, row, index){
        if(row.status==2){
            return '<span class="label label-info">'+value+'</span>';
        }else if(row.status==3){
            return '<span class="label label-warning">'+value+'</span>';
        }else if(row.status==5){
            return '<span class="label label-success">'+value+'</span>';
        }else if(row.status==6){
            return '<span class="label label-default">'+value+'</span>';
        }else{
            return '<span class="label label-danger">'+value+'</span>';
        }
    }
    function operateFormatter(value, row, index){
      var ele = [
        '<a class="logdetail" data-url="'+row.url+'">查看详情</a>'
      ]
      return ele.join('');
    }
    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    } 
  }
  /**
  *加载平台tab
  **/
  tabFunc.prototype.platinit = function(id,appid){
    var type = "plat";
    var app = id;
    // console.log(app)
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();
    // console.log(url)
    var it = $(app).find("#plat_table");
    loadlog(it,tab.val())
    function loadlog(it,url){
      it.bootstrapTable({
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        // dataField:'rows',
        // maintainSelected:true,//在更改和搜索时保持选定的行
        // searchOnEnterKey:"true",
        columns: [
           {
               field: 'state',
               checkbox: true,
               align: 'center',
               valign: 'middle'
           }, {
               field: 'platid',
               title: 'ID',
               searchable:true,
               sortable: true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           },
           {
               field: 'platname',
               title: '平台名',
               sortable: true,
               searchable:true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           }, {
               field: 'officials',
               title: '平台负责人',
               sortable: true,
               searchable:true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           }, {
               field: 'platalias',
               title: '平台别名',
               sortable: true,
               searchable:true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           }, {
               field: 'virtdomain',
               title: '业务域名',
               sortable: true,
               searchable:true,
               // footerFormatter: platsiteformatter,
               align: 'center'
           }, {
               field: 'created_at',
               title: '创建时间',
               sortable: true,
               align: 'center',
           }
         ],
      });
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
    }
      
    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }
      // initplattable($("#"+commonapp).find("#plat_table"),"plat");
    var commonapp = localStorage.getItem("currentapp").split("#")[1];
    $("#"+commonapp).delegate("#"+commonapp+"_addplatgamebtn","click",function(e){
      // console.log(localStorage.getItem("currentapp"))
      tabss[localStorage.getItem("currentapp")].showp(e,'addplattogame',function(){
      });
    })
  }
  /**
  *加载角色tab
  **/
  tabFunc.prototype.roleinit = function(id,appid){
    var commonapp = id.split("#")[1];
    $("#"+commonapp).delegate("#"+commonapp+"_addrole","click",function(e){
      tabss[localStorage.getItem("currentapp")].showp(e,'addrole');
    })
    var type = "role";
    var app = id;
    var tab = $(app).find("input[data-type='"+type+"']");
    var url = tab.val();
    var selections = [];
    var updaterole = {
      'click .btn':function(e, value, row, index){
        tabss[app].$set("platcreateurls.updateapprole","/"+localStorage.getItem("currentappid")+"/roles/"+row.uuid+"/update");
        tabss[app].showp(e,e.target.id.split("_")[1]);
      }
    }

    loadrole($(app).find("#role_table"),url);
    function loadrole(it,url){

      it.bootstrapTable({
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        // dataField:'rows',
        // maintainSelected:true,//在更改和搜索时保持选定的行
        // searchOnEnterKey:"true",
        columns: [
           {
               field: 'state',
               checkbox: true,
               align: 'center',
               valign: 'middle'
           }, {
               field: 'name',
               title: '角色名',
               sortable: true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           },
           {
               field: 'staff',
               title: '应用管理员',
               sortable: true,
               footerFormatter: stafffommater,
               align: 'center'
           }, {
               field: 'rexec',
               title: '执行权限',
               sortable: true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           }, {
               field: 'created_user',
               title: '创建用户',
               sortable: true,
               // footerFormatter: totalNameFormatter,
               align: 'center'
           }, {
               field: 'created_at',
               title: '创建时间',
               sortable: true,
               align: 'center',
           },{
              field:'operate',
              title:'操作',
              align:'center',
              formatter:rolesupdate,
              events:updaterole
          }
         ],
      });
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
        tabss[app].$set("selecteddel.approle",selections);
        if(selections.length==1){
          tabss[app].$set("deletebtn.approle",true);
        }else{
          tabss[app].$set("deletebtn.approle",true);
        }
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });

      function rolesupdate(value,row,index){
        var ele = $(modaltpl("updateapprole",["更新","更新应用"]));
        tabss[app].$compile(ele.get(0));
        ele.find(".modal-dialog").addClass("dialog-init").wsresizable();
        // console.log($(app).find(".modal").css("z-index"))
        ele.find(".modal-dialog").css("z-index",1050+5);
        ele.find(".modal").wsdraggable({handle:'.modal-header'});
        ele.find(".modal").appendTo($("body"));
        tabss[app].$set("target.updateapprole",ele.find(".modal-dialog"));

        return ele.find(".btn:first")[0].outerHTML;
      }  
    }
    function stafffommater(value){
      return value==1?"是":"否";
    }
      
    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }
  }
  /**
  *加载域名tab
  **/
  tabFunc.prototype.domaininit = function(id,appid){
    var domainchild = new Vue({
      el:"#domainmanage",
      data:function(){
        return {
          // disabled:[],
          value:'',
          format:['yyyy-MM-dd'],
          reset:true
        }
      }
    })
  }
/**
*每个tab下内部的方法
**/
  function tabchildfunc(){};
  tabchildfunc.prototype.workflowadd = function(){
      $(".workflows input[type='checkbox']").parents(".form-group").find("label").attr("class","col-md-9")
      $(".workflows input[type='checkbox']").parent().attr("class","col-md-3");
      var commonapp = localStorage.getItem("currentapp").split("#")[1];
      sortid();
      function cloneMore(selector, type) {
          var form = $('#'+commonapp+'_addworkflow_manage form');
          var total = parseInt(form.find('input[name="form-TOTAL_FORMS"]').val());
          total++;
          var length = $("#"+commonapp+"_addworkflow_manage form").find(".widget-content").length;
          $('#id_' + type + '-TOTAL_FORMS').val(total);
          var newElement = $(selector).clone(true);
          newElement.find('input').each(function() {
              var name = $(this).attr('name').replace('-' + (length-1) + '-','-' + length + '-');
              var id = 'id_' + name;
              if(name.indexOf("stepid")>-1){
                  $(this).val($("#"+commonapp+"_addworkflow_manage form").find(".widget-content").length+1)
              }
              $(this).attr({'name': name, 'id': id}).removeAttr('checked');
          });
          newElement.find('select').each(function() {
              var newFor = $(this).attr('name').replace('-' + (length-1) + '-','-' + length + '-');
              $(this).attr({'name':newFor,id:'_id'+newFor});
          });
          newElement.find('label').each(function() {
              var newFor = $(this).attr('for').replace('-' + (length-1) + '-','-' + length + '-');
              $(this).attr('for', newFor);
          });
          $(selector).after(newElement);
          sortid();
      }
      $('#add_more').click(function() {
          cloneMore('.widget-content:last', 'service');
      });
      $(".widget-content .delete_widget").click(function(){
          if($("#"+commonapp+"_addworkflow_manage form").find(".widget-content").length>1){
            $(this).parents(".widget-content").remove();
            sortid();
          }
      })
      $(".widget-content").sorts({
          beforeDrag:function(evt,el){
              if(evt.target.className.indexOf("move_widget")==-1){
                  return false;
              }
          },
          onDrag:function(evt,el){
              if(evt.target.className.indexOf("move_widget")==-1){
                  return false;
              }
          },
          onDrop:function(evt,el){
              sortid();
          }
      })
      function sortid(){
          var commonapp = localStorage.getItem("currentapp").split("#")[1];
          var con = $("#"+commonapp+"_addworkflow_manage form").find(".widget-content");
          for(var i=0;i<con.length;i++){
              var count = i+1;
              $(con[i]).find('input').each(function() {
                  var name = $(this).attr('name').replace(/\d+/g,i);
                  var id = 'id_' + name;
                  if(name.indexOf("stepid")>-1){
                      $(this).val($("#"+commonapp+"_addworkflow_manage form").find(".widget-content").length+1)
                  }
                  $(this).attr({'name': name, 'id': id}).removeAttr('checked');
              });
              $(con[i]).find('select').each(function() {
                  var newFor = $(this).attr('name').replace(/\d+/g,i);
                  $(this).attr({'name':newFor,id:'_id'+newFor});
              });
              $(con[i]).find('label').each(function() {
                  var newFor = $(this).attr('for').replace(/\d+/g,i);
                  $(this).attr('for', newFor);
              });
              $(con[i]).find("input[type='number']").val(count).attr('readonly','readonly');
          }

          $("#"+commonapp+"_addworkflow_manage form").find('input[name="form-TOTAL_FORMS"]').val(con.length);
      }
  }
/**
*加载CMDB页面
**/
  function loadcmdb(id,apps,appid){
    $.ajax({
      url:"/api/cmdb/menu",
      type:"get",
      dataType:"json",
      success:function(data){
        apps.$set("cmdbtab",data);
        window.localStorage.setItem("cmdbappid",id);
        window.localStorage.setItem("cmdbid",appid);

        //获取监控相关数据支持
        $.ajax({
          url:"/api/hosts/monitor",
          type:"get",
          dataType:"json",
          success:function(data){
            // console.log(data);
            var temp = [],proxy = [],group = [];
            if(data.templates){
              for(var i=0;i<data.templates.length;i++){
                temp.push({"value":data.templates[i].templateid,"label":data.templates[i].name});
              }
            }
            if(data.proxys){
              for(var i=0;i<data.proxys.length;i++){
                proxy.push({"value":data.proxys[i].proxyid,"label":data.proxys[i].host});
              }
            }
            if(data.groups){
              for(var i=0;i<data.groups.length;i++){
                group.push({"value":data.groups[i].groupid,"label":data.groups[i].name});
              }
            }
            apps.$set("monitors.templates",temp);
            apps.$set("monitors.proxys",proxy);
            apps.$set("monitors.groups",group);
          }
        })

        locacmdbdashboard("api/users/widgets");
      }
    });

  }
  var leftbar = $("#left-nav");
  leftbar.delegate("ul>li a","click",function(){
    var t = $(this).parent();
    t.parent().find(".active").removeClass('active');
    t.toggleClass('active');
    var target = t.attr("data-target");
    apps.$set("cmdbactive",target);
    // console.log(target)
    if(target=="dashboard"){setTimeout(function(){locacmdbdashboard(t.attr("data-url"));},100)}    
    if(target=="instance"){setTimeout(function(){apps.$set("entryshow",false);loadtree(t.attr("data-url"));},100)}
    if(target=="location"){setTimeout(function(){loadtree(t.attr("data-url"));},100)}
    if(target=="group"){setTimeout(function(){loadgroup(t.attr("data-url"));},100)}
    if(target=="accelerate"){setTimeout(function(){loadaccelerate(t.attr("data-url"));},100)}
    if(target=="division"){setTimeout(function(){loaddivision(t.attr("data-url"));},100)}
    if(target=="idc"){setTimeout(function(){loadidc(t.attr("data-url"));},100)}
    if(target=="cdn"){setTimeout(function(){loadcdn(t.attr("data-url"));},100)}
    if(target=="contract"){setTimeout(function(){loadcontract(t.attr("data-url"));},100)}
    if(target=="domain"){setTimeout(function(){loaddomain(t.attr("data-url"));},100)}
    if(target=="resolve"){setTimeout(function(){loadresolve(t.attr("data-url"));},100)}
  });

  
  /*加载cmdb的表格*/
  function loadcmdbtable(url){
    apps.$set("entryshow",true);
    $("#selecttimez input").datetimepicker({
                        formatTime:'H:i',
                          formatDate:'Y-m-d',
                          timepickerScrollbar:false
                          ,step:5,
                          lang:'ch'});

    var it = $("#cmdb_table");
    // loadcmd(it,url)
    $("#buttons").delegate("#enablemonitor","click",function(){
      $.ajax({
        url:"/api/hosts/monitor/enable/",
        type:"post",
        dataType:"json",
        data:{uuids:apps.$get("cmdbselected").join(",")},
        success:function(data){
          if(data.success){
            toastr.success(data.msg,"成功");
          }else{
            toastr.error(data.msg,"失败");
          }
        }
      })
    }).delegate("#disablemonitor","click",function(){
      $.ajax({
        url:"/api/hosts/monitor/disable/",
        type:"post",
        dataType:"json",
        data:{uuids:apps.$get("cmdbselected").join(",")},
        success:function(data){
          if(data.success){
            toastr.success(data.msg,"成功");
          }else{
            toastr.error(data.msg,"失败");
          }
        }
      })
    })

    var clickid;

    function loadmonitorone(id){
      clickid = id;
      $.ajax({
        url:"/api/hosts/"+id+"/monitor/",
        type:"get",
        dataType:"json",
        success:function(data){
          // console.log(data)
          var dg = data.graphs;
          // console.log(dg)
          var usl = [],selecttps = [];
          for(var i=0;i<data.graphs.length;i++){
                usl.push({name:dg[i].name,url:"/api/hosts/graph"+urlincode(dg[i])});
          }
          for(var i=0;i<data.linked_templates.length;i++){
              selecttps.push(data.linked_templates[i].templateid);
          }
          apps.$set("monitorimg",usl);
          apps.$set("cmdbselectedtpl",selecttps);

          
        }
      })
    }


    function loadaudit(id){
      $.ajax({
        url:"/api/audit/"+id+"/logs/",
        type:"get",
        dataType:"json",
        success:function(data){
          // console.log(data);
          apps.$set("cmdbselectedaudit",data.results);
        }
      })
    }

    $(".customtab ul.nav-tabs li").click(function(){
      $(".customtab ul.nav-tabs li").removeClass('active');
      var t = $(this);
      t.addClass('active');
      if(t.attr("data-target")=="#history"){
        loadaudit(clickid);
      }
      t.parents(".customtab").find(".tab-content").find(".tab-pane").removeClass('active');
      t.parents(".customtab").find(".tab-content").find(t.attr("data-target")).addClass('active');
    })
    var monEvent = {
      'click .monitor': function(e, value, row, index){
        // console.log(row)
        if(!$("#idccabinet").hasClass('active')){
          $("#idccabinet").addClass("active");
        }
        $("#logmainpage").css("height",$("#logmainpage").parents(".modal-body")[0].offsetHeight-$("#logmainpage")[0].getBoundingClientRect().top);
          loadmonitorone(row.uuid);
      },
    }

    $("#idccabinet").find(".widget-icons").click(function(){
      $("#idccabinet").removeClass('active');
    })

    $("#appmodaladdmonitor").css("position","relative").appendTo($("body"));
    apps.targetcmdb["addmonitor"] = $("#appmodaladdmonitor").find(".modal-dialog");
    apps.$set("cmdbs.addmonitor.name","添加监控");
    $("#appmodaladdmonitor form").submit(function(e){
      e.preventDefault();
      var t = $(this);
      var obj = {
        "templateids":apps.$get("cmdbselectedtpl").join(","),
        "groupid":apps.$get("cmdbselectedgroup")[0],
        "proxy_hostid":apps.$get("cmdbselectedproxy")[0]
      }
      var type = apps.$get("cmdbselectedtpl").length>0?"put":"post";
      $.ajax({
        url:"/api/hosts/"+apps.$get("cmdbselected")[0]+"/monitor",
        type:type,
        dataType:"json",
        data:obj,
        success:function(data){
          if(data.success){
            toastr.success(data.msg,"成功");
          }else{
            toastr.error(data.msg,"失败");
          }
          t.parents(".modal").find(".close").click();
        }
      })
    })


    $("#appmodalcmdbentry").css("position","relative").appendTo($("body"));
    apps.targetcmdb["cmdbentry"] = $("#appmodalcmdbentry").find(".modal-dialog");
    apps.$set("cmdbs.cmdbentry.name","录入");
    $("#appmodalcmdbentry").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodalcmdbentry").wsdraggable({handle:'.modal-header'});

    // apps.$set("cmdbs.addmonitor.url","cmdb/idc/create/");
    $("#appmodaladdmonitor").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodaladdmonitor").wsdraggable({handle:'.modal-header'});
    
      $("#appmodalcmdbupdate").css("position","relative").appendTo($("body"));
      apps.targetcmdb["cmdbupdate"] = $("#appmodalcmdbupdate").find(".modal-dialog");
      apps.$set("cmdbs.cmdbupdate.name","更新资产");
      $("#appmodalcmdbupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
      $("#appmodalcmdbupdate").wsdraggable({handle:'.modal-header'});
      it.bootstrapTable('destroy');
      it.bootstrapTable({
        // height:getHeight(it),
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        // dataField:'rows',
        // maintainSelected:true,//在更改和搜索时保持选定的行
        // searchOnEnterKey:"true",
        columns: [
          {
              field: 'state',
              checkbox: true,
              align: 'center',
              valign: 'middle'
          },{
              field: 'public_ip',
              title: '公网IP',
              sortable: true,
              searchable:true,
              events: monEvent,
              formatter: operateFormatter,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          }, {
              field: 'agent_status',
              title: '客户端状态',
              searchable:true,
              sortable: true,
              formatter: agent_status_Formatter,
              align: 'center'
          },{
              field: 'app_detail',
              title: '应用详情',
              sortable: true,
              searchable:true,
              // footerFormatter: totalNameFormatter,
              align: 'center'
          },{
              field: 'division',
              title: '所属部门',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'app',
              title: '所属应用',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'platform',
              title: '所属平台',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'app_mode',
              title: '应用类型',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'asset_family',
              title: '宿主机',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'asset_model',
              title: '服务器型号',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'memory_capacity',
              title: '内存容量',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'cpu_core',
              title: 'CPU核数',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'disk_capacity',
              title: '硬盘容量',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'disk_number',
              title: '硬盘数量',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'expire',
              title: '是否在保',
              sortable: true,
              searchable: true,
              formatter: expire_Formatter,
              align: 'center'
          },{
              field: 'source',
              title: '服务器来源',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'status',
              title: '服务器状态',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'contract',
              title: '合同',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'cost_person',
              title: '成本担当人',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'cpu_brand',
              title: 'CPU品牌',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'expire_date',
              title: '过保时间',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'launch_person',
              title: '上架人',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'launch_date',
              title: '上架日期',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'os_family',
              title: '操作系统版本',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'purchase_cost',
              title: '费用消耗',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'raid_type',
              title: 'Raid类型',
              sortable: true,
              searchable: true,
              align: 'center'
          },{
              field: 'serial_number',
              title: '序列号',
              sortable: true,
              searchable: true,
              align: 'center'
          }
        ],
      });
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
        apps.$set("cmdbselected",selections);

        if(selections.length>0){
           apps.$set("deletebtn.hostdown",true);
         }else{
           apps.$set("deletebtn.hostdown",false);
         }
        if(selections.length==0){
          apps.$set("cmdbs.addmonitor.showif",false);
          apps.$set("cmdbs.cmdbupdate.url",null);
          apps.$set("cmdbs.enablemon.url",null);
        }
        if(selections.length>0){
          apps.$set("cmdbs.enablemon.url","api/hosts/monitor/enable/");
          apps.$set("cmdbs.disablemon.url","api/hosts/monitor/disable/");
        }
        if(selections.length>1){
          apps.$set("cmdbs.addmonitor.showif",false);
          apps.$set("cmdbs.cmdbupdate.url","cmdb/hosts/bulk/update");
        }
        if(selections.length==1){
          // console.log(selections)
          loadmonitorone(selections[0]);
          apps.$set("cmdbs.addmonitor.showif",true);
          apps.$set("cmdbs.cmdbupdate.url","cmdb/hosts/"+selections[0]+"/update/");
        }
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
      function operateFormatter(value, row, index){
        var ele = [
          '<a class="monitor" title="查看监控">'+value+'</a>'
        ]
        return ele.join('');
      }
    setTimeout(function () {
        // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
        //   var that = $(this);
        //   that.parent().toggleClass('open');
        //   $(document).mousedown(function(event){
        //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
        //       that.parent().removeClass('open');
        //     }
        //   })
        // });
    }, 200);

    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }
    function expire_Formatter(value,row,index){
      return value?'<i class="glyphicon glyphicon-remove" style="color:red"></i>':'<i style="color:#39adb4" class="glyphicon glyphicon-ok"></i>';
    }
    function agent_status_Formatter(value,row,index){
      return value?'<i style="color:#39adb4" class="glyphicon glyphicon-ok"></i>':'<i class="glyphicon glyphicon-remove" style="color:red"></i>';
    }

    $("#assetsearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/hosts?search="+val});
      }
    })

  }
  /*点击加载cmdb树*/
  function loadtree(url){
    var id = window.localStorage.getItem("cmdbappid");
    var tree = url.indexOf("division")>-1?$(id).find("#instance_tree"):$(id).find("#location_tree");
    $.ajax({
      url:url,
      type:"get",
      dataType:"json",
      success:function(treedata){
        tree.fancytree({
            source:treedata,
            extensions: ["dnd"],
            quicksearch:true,
            dnd: {
                  preventVoidMoves: true, // Prevent dropping nodes 'before self', etc.
                  preventRecursiveMoves: true, // Prevent dropping nodes on own descendants
                  autoExpandMS: 400,
                  refreshPositions: true,
                  draggable: {
                    appendTo: "body",  // We don't want to clip the helper inside container
                    // scroll: false,
                    // containment: "parent",  // $("ul.fancytree-container"),
                    // cursorAt: { left: 5 },55
                    revert: "invalid"
                    // revert: function(dropped) {
                    //   return
                    // }
                  },
                  dragStart: function(node, data) {
                    // allow dragging `node`:
                    return true;
                  },
                  dragEnter: function(node, data) {
                     return true;
                  },
                  initHelper: function(node, data) {
                    // Helper was just created: modify markup
                    var helper = data.ui.helper,
                      sourceNodes = data.tree.getSelectedNodes();

                    // Store a list of active + all selected nodes
                    if( !node.isSelected() ) {
                      sourceNodes.unshift(node);
                    }
                    helper.data("sourceNodes", sourceNodes);
                    // Mark selected nodes also as drag source (active node is already)
                    $(".fancytree-active,.fancytree-selected", tree.$container)
                      .addClass("fancytree-drag-source");
                    // Add a counter badge to helper if dragging more than one node
                    if( sourceNodes.length > 1 ) {
                      helper.append($("<span class='fancytree-childcounter'/>")
                        .text("+" + (sourceNodes.length - 1)));
                    }
                    // Prepare an indicator for copy-mode
                    helper.prepend($("<span class='fancytree-dnd-modifier'/>")
                      .text("+").hide());
                  },
                  updateHelper: function(node, data) {
                    // Mouse was moved or key pressed: update helper according to modifiers

                    // NOTE: pressing modifier keys stops dragging in jQueryUI 1.11
                    // http://bugs.jqueryui.com/ticket/14461
                    var event = data.originalEvent,
                      tree = node.tree,
                      copyMode = event.ctrlKey || event.altKey;

                    // Adjust the drop marker icon
                //          data.dropMarker.toggleClass("fancytree-drop-copy", copyMode);

                    // Show/hide the helper's copy indicator (+)
                    data.ui.helper.find(".fancytree-dnd-modifier").toggle(copyMode);
                    // tree.debug("1", $(".fancytree-active,.fancytree-selected", tree.$container).length)
                    // tree.debug("2", $(".fancytree-active,.fancytree-selected").length)
                    // Dim the source node(s) in move-mode
                    $(".fancytree-drag-source", tree.$container)
                      .toggleClass("fancytree-drag-remove", !copyMode);
                    // data.dropMarker.toggleClass("fancytree-drop-move", !copyMode);
                  },
                  dragDrop: function(node, data) {
                    var sourceNodes = data.ui.helper.data("sourceNodes"),
                      event = data.originalEvent,
                      copyMode = event.ctrlKey || event.altKey;

                    if( copyMode ) {
                      $.each(sourceNodes, function(i, o){
                        o.copyTo(node, data.hitMode, function(n){
                          delete n.key;
                          n.selected = false;
                          n.title = "Copy of " + n.title;
                        });
                      });
                    }else{
                      $.each(sourceNodes, function(i, o){
                        o.moveTo(node, data.hitMode);
                      });
                    }
                  }
                },
                focus: function(event, data) {
              var node = data.node;
              // Auto-activate focused node after 1 second
              if(node.data.url){
                node.scheduleAction("activate", 1000);
              }
            },
            blur: function(event, data) {
              data.node.scheduleAction("cancel");
            },
            activate: function(event, data){
              var node = data.node,
                orgEvent = data.originalEvent || {};
              if(node.data.url){
                
                // $.ajax({
                //  url:node.data.url,
                //  type:"get",
                //  dataType:"json",
                //  success:function(data){
                    // loadhost($(app).find("#hosttable"),node.data.url);
                  // }
                // })
              }
            },
            click: function(event, data){ // allow re-loads
              var node = data.node,
                orgEvent = data.originalEvent;
                // console.log(node.data)
                if(data.originalEvent.target.className.indexOf("fancytree-expander")==-1){
                  if(node.data.url){
                    loadcmdbtable(node.data.url);
                    // $(app).find("#hosttable").bootstrapTable('destroy');
                    // loadhost($(app).find("#hosttable"),node.data.url);
                    // data.tree.reactivate();
                    // window.open(node.data.href, (orgEvent.ctrlKey || orgEvent.metaKey) ? "_blank" : node.data.target);
                  }
                } 
            }   
        });
      }
    })
  }
  /*点击加载组*/
  function loadgroup(url){
    var it = $("#hostgroup_table");
   // loadcmd(it,url)

   // var getupdatecmd = {
   //   'click .btn':function(e, value, row, index){
   //     console.log(e.target.id.split("_")[1])
   //     tabss[app].$set("platcreateurls.updatecmd",row.url);
   //     tabss[app].showp(e,e.target.id.split("_")[1]);
   //   }
   // }
     it.bootstrapTable('destroy');
     it.bootstrapTable({
       sidePagination:"server",
       url:url,
       queryParams:queryParams,
       responseHandler:responseHandler,
       columns: [],
     });
     it.on('check.bs.table uncheck.bs.table ' +
           'check-all.bs.table uncheck-all.bs.table', function () {
       selections = getIdSelections(it);
     });
     it.on('all.bs.table', function (e, name, args) {
       
     });
   // }
   setTimeout(function () {
       // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
       //   var that = $(this);
       //   that.parent().toggleClass('open');
       //   $(document).mousedown(function(event){
       //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
       //       that.parent().removeClass('open');
       //     }
       //   })
       // });
   }, 200);

   function getIdSelections(it) {
       return $.map(it.bootstrapTable('getSelections'), function (row) {
           return row.uuid
       });
   }
   function getHeight(it) {
       return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
   }
  }
  function loadaccelerate(url){
    var it = $("#accelerate_table");
   // loadcmd(it,url)

   // var getupdatecmd = {
   //   'click .btn':function(e, value, row, index){
   //     console.log(e.target.id.split("_")[1])
   //     tabss[app].$set("platcreateurls.updatecmd",row.url);
   //     tabss[app].showp(e,e.target.id.split("_")[1]);
   //   }
   // }
    $("#appmodalacceupdate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["acceupdate"] = $("#appmodalacceupdate").find(".modal-dialog");
    apps.$set("cmdbs.acceupdate.name","更新部门");
    $("#appmodalacceupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodalacceupdate").wsdraggable({handle:'.modal-header'});
    $("#appmodalaccecreate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["accecreate"] = $("#appmodalaccecreate").find(".modal-dialog");
    apps.$set("cmdbs.accecreate.name","创建部门");
    apps.$set("cmdbs.accecreate.url","cmdb/accelerate/create/");
    $("#appmodalaccecreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodalaccecreate").wsdraggable({handle:'.modal-header'});
     it.bootstrapTable('destroy');
     it.bootstrapTable({
       sidePagination:"server",
       url:url,
       queryParams:queryParams,
       responseHandler:responseHandler,
       columns: [
       {
           field: 'state',
           checkbox: true,
           align: 'center',
           valign: 'middle'
       },{
           field: 'domain',
           title: '域名',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       },{
           field: 'cname',
           title: 'CNAME',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       },{
           field: 'division',
           title: '所属部门',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'app',
           title: '所属应用',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       },{
           field: 'company',
           title: 'CDN厂商',
           sortable: true,
           searchable:true,
           align: 'center'
       },{
           field: 'created_at',
           title: '创建时间',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }],
     });
     it.on('check.bs.table uncheck.bs.table ' +
           'check-all.bs.table uncheck-all.bs.table', function () {
       selections = getIdSelections(it);
       apps.$set("selectedde.acce",selections);
       if(selections.length>0){
          apps.$set("deletebtn.acce",true);
        }else{
          apps.$set("deletebtn.acce",false);
        }

       if(selections.length==0){
         apps.$set("cmdbs.acceupdate.url",null);
       }
       if(selections.length>1){
         apps.$set("cmdbs.acceupdate.url",null);
       }
       if(selections.length==1){
         apps.$set("cmdbs.acceupdate.url","cmdb/accelerate/"+selections[0]+"/update/");
       }
     });
     it.on('all.bs.table', function (e, name, args) {
       
     });
   // }
   setTimeout(function () {
       // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
       //   var that = $(this);
       //   that.parent().toggleClass('open');
       //   $(document).mousedown(function(event){
       //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
       //       that.parent().removeClass('open');
       //     }
       //   })
       // });
   }, 200);

   function getIdSelections(it) {
       return $.map(it.bootstrapTable('getSelections'), function (row) {
           return row.uuid
       });
   }
   function getHeight(it) {
       return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
   }

    $("#acceleratesearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/accelerates?search="+val});
      }
    })
  }
  function loaddivision(url){
    var it = $("#division_table");
    // console.log(it)
   // loadcmd(it,url)

   // var getupdatecmd = {
   //   'click .btn':function(e, value, row, index){
   //     console.log(e.target.id.split("_")[1])
   //     tabss[app].$set("platcreateurls.updatecmd",row.url);
   //     tabss[app].showp(e,e.target.id.split("_")[1]);
   //   }
   // }
     // it.bootstrapTable('destroy');
     $("#appmodaldivisionupdate").css("position","relative").appendTo($("body"));
     apps.targetcmdb["divisionupdate"] = $("#appmodaldivisionupdate").find(".modal-dialog");
     apps.$set("cmdbs.divisionupdate.name","更新部门");
     $("#appmodaldivisionupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
     $("#appmodaldivisionupdate").wsdraggable({handle:'.modal-header'});
     $("#appmodaldivisioncreate").css("position","relative").appendTo($("body"));
     apps.targetcmdb["divisioncreate"] = $("#appmodaldivisioncreate").find(".modal-dialog");
     apps.$set("cmdbs.divisioncreate.name","创建部门");
     apps.$set("cmdbs.divisioncreate.url","cmdb/division/create/");
     $("#appmodaldivisioncreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
     $("#appmodaldivisioncreate").wsdraggable({handle:'.modal-header'});
     it.bootstrapTable({
       sidePagination:"server",
       url:url,
       queryParams:queryParams,
       responseHandler:responseHandler,
       columns: [
       {
           field: 'state',
           checkbox: true,
           align: 'center',
           valign: 'middle'
       },{
           field: 'name',
           title: '名称',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'created_at',
           title: '创建时间',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }],
     });
     it.on('check.bs.table uncheck.bs.table ' +
           'check-all.bs.table uncheck-all.bs.table', function () {
       selections = getIdSelections(it);
       if(selections.length==0){
         apps.$set("cmdbs.divisionupdate.url",null);
       }
       if(selections.length>1){
         apps.$set("cmdbs.divisionupdate.url",null);
       }
       if(selections.length==1){
         apps.$set("cmdbs.divisionupdate.url","cmdb/division/"+selections[0]+"/update/");
       }
     });
     it.on('all.bs.table', function (e, name, args) {
       
     });
   // }
   // setTimeout(function () {
   //     $("[data-tab='division']").delegate(".dropdown-toggle","click",function(){
   //       var that = $(this);
   //       console.log("asdfasdf")
   //       that.parent().addClass('open');
   //     });
   // },300);

   function getIdSelections(it) {
       return $.map(it.bootstrapTable('getSelections'), function (row) {
           return row.uuid
       });
   }
   function getHeight(it) {
       return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
   }
    $("#divisionsearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/divisions?search="+val});
      }
    })
  }
  function loadidc(url){
    var it = $("#idc_table");
   // loadcmd(it,url)
    var logEvent = {
      'click .idcdetail': function(e, value, row, index){
        if(!$("#idccabinet").hasClass('active')){
          $("#idccabinet").addClass("active");
        }

        $.ajax({
          url:"/api/getcabinet?idc_id="+row.uuid,
          type:"get",
          dataType:"json",
          success:function(data){
            var dtai1 = data.results;
            var cab = $("#cabinet_table");
            cab.bootstrapTable('destroy');
            cab.bootstrapTable({
              data:dtai1,
              columns: [{
                  field: 'state',
                  checkbox: true,
                  align: 'center',
                  valign: 'middle'
              },{
                  field: 'name',
                  title: '机柜名称',
                  sortable: true,
                  searchable:true,
                  align: 'center'
              },{
                  field: 'remark',
                  title: '备注',
                  searchable:true,
                  sortable: true,
                  align: 'center'
              }],
            });

            cab.on('check.bs.table uncheck.bs.table ' +
                  'check-all.bs.table uncheck-all.bs.table', function () {
              selections = getIdSelections(it);
              if(selections.length==0){
                apps.$set("cmdbs.cabupdate.url",null);
              }
              if(selections.length>1){
                apps.$set("cmdbs.cabupdate.url",null);
              }
              if(selections.length==1){
                apps.$set("cmdbs.cabupdate.url","cmdb/cabinet/"+selections[0]+"/update/");
              }
            });
            cab.on('all.bs.table', function (e, name, args) {
              
            });


          }
        })
      },
    }

    $("#idccabinet .glyphicon-remove").click(function(){
      $("#idccabinet").removeClass("active");
    })
   // var getupdatecmd = {
   //   'click .btn':function(e, value, row, index){
   //     console.log(e.target.id.split("_")[1])
   //     tabss[app].$set("platcreateurls.updatecmd",row.url);
   //     tabss[app].showp(e,e.target.id.split("_")[1]);
   //   }
   // }
      $("#appmodalcabupdate").css("position","relative").appendTo($("body"));
      apps.targetcmdb["cabupdate"] = $("#appmodalcabupdate").find(".modal-dialog");
      apps.$set("cmdbs.cabupdate.name","更新机柜");
      $("#appmodalcabupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
      $("#appmodalcabupdate").wsdraggable({handle:'.modal-header'});

      $("#appmodalidcupdate").css("position","relative").appendTo($("body"));
      apps.targetcmdb["idcupdate"] = $("#appmodalidcupdate").find(".modal-dialog");
      apps.$set("cmdbs.idcupdate.name","更新资产");
      $("#appmodalidcupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
      $("#appmodalidcupdate").wsdraggable({handle:'.modal-header'});
      $("#appmodalidccreate").css("position","relative").appendTo($("body"));
      apps.targetcmdb["idccreate"] = $("#appmodalidccreate").find(".modal-dialog");
      apps.$set("cmdbs.idccreate.name","更新资产");
      apps.$set("cmdbs.idccreate.url","cmdb/idc/create/");
      $("#appmodalidccreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
      $("#appmodalidccreate").wsdraggable({handle:'.modal-header'});

      $("#appmodalcabinetcreate").css("position","relative").appendTo($("body"));
      apps.targetcmdb["cabinetcreate"] = $("#appmodalcabinetcreate").find(".modal-dialog");
      apps.$set("cmdbs.cabinetcreate.name","创建机柜");
      apps.$set("cmdbs.cabinetcreate.url","cmdb/cabinet/create/");
      $("#appmodalcabinetcreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
      $("#appmodalcabinetcreate").wsdraggable({handle:'.modal-header'});
     it.bootstrapTable('destroy');
     it.bootstrapTable({
       sidePagination:"server",
       url:url,
       queryParams:queryParams,
       responseHandler:responseHandler,
       columns: [{
           field: 'state',
           checkbox: true,
           align: 'center',
           valign: 'middle'
       }, {
           field: 'idc_region',
           title: '机房',
           searchable:true,
           sortable: true,
           events: logEvent,
           formatter: operateFormatter,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       },{
           field: 'idc',
           title: 'IDC厂商',
           sortable: true,
           searchable:true,
           events: logEvent,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'idc_area',
           title: 'IDC区域',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'idc_address',
           title: 'IDC地址',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'remark',
           title: '备注',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }],
     });

      function operateFormatter(value, row, index){
        var ele = [
          '<a class="idcdetail" title="查看机柜" data-id="'+row.uuid+'">'+value+'</a>'
        ]
        return ele.join('');
      }
     it.on('check.bs.table uncheck.bs.table ' +
           'check-all.bs.table uncheck-all.bs.table', function () {
       selections = getIdSelections(it);
       if(selections.length==0){
         apps.$set("cmdbs.idcupdate.url",null);
       }
       if(selections.length>1){
         apps.$set("cmdbs.idcupdate.url",null);
       }
       if(selections.length==1){
         apps.$set("cmdbs.idcupdate.url","cmdb/idc/"+selections[0]+"/update/");
       }
     });
     it.on('all.bs.table', function (e, name, args) {
       
     });
   // }
   setTimeout(function () {
       // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
       //   var that = $(this);
       //   that.parent().toggleClass('open');
       //   $(document).mousedown(function(event){
       //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
       //       that.parent().removeClass('open');
       //     }
       //   })
       // });
   }, 200);

   function getIdSelections(it) {
       return $.map(it.bootstrapTable('getSelections'), function (row) {
           return row.uuid
       });
   }
   function getHeight(it) {
       return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
   }
    $("#idcsearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/idcs?search="+val});
      }
    })
  }
  function loadcdn(url){
    var it = $("#cdn_table");
   // loadcmd(it,url)

   // var getupdatecmd = {
   //   'click .btn':function(e, value, row, index){
   //     console.log(e.target.id.split("_")[1])
   //     tabss[app].$set("platcreateurls.updatecmd",row.url);
   //     tabss[app].showp(e,e.target.id.split("_")[1]);
   //   }
   // }
    $("#appmodalcdnupdate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["cdnupdate"] = $("#appmodalcdnupdate").find(".modal-dialog");
    apps.$set("cmdbs.cdnupdate.name","更新CDN厂商");
    $("#appmodalcdnupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodalcdnupdate").wsdraggable({handle:'.modal-header'});
    $("#appmodalcdncreate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["cdncreate"] = $("#appmodalcdncreate").find(".modal-dialog");
    apps.$set("cmdbs.cdncreate.name","创建CDN厂商");
    apps.$set("cmdbs.cdncreate.url","cmdb/cdn/create/");
    $("#appmodalcdncreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodalcdncreate").wsdraggable({handle:'.modal-header'});
     it.bootstrapTable('destroy');
     it.bootstrapTable({
       sidePagination:"server",
       url:url,
       queryParams:queryParams,
       responseHandler:responseHandler,
       columns: [{
           field: 'state',
           checkbox: true,
           align: 'center',
           valign: 'middle'
       },{
           field: 'name',
           title: '名称',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'manage',
           title: '管理页面',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'created_at',
           title: '创建时间',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }],
     });
     it.on('check.bs.table uncheck.bs.table ' +
           'check-all.bs.table uncheck-all.bs.table', function () {
       selections = getIdSelections(it);
       apps.$set("selectedde.cdn",selections);
       if(selections.length>0){
          apps.$set("deletebtn.cdn",true);
        }else{
          apps.$set("deletebtn.cdn",false);
        }
       if(selections.length==0){
         apps.$set("cmdbs.cdnupdate.url",null);
       }
       if(selections.length>1){
         apps.$set("cmdbs.cdnupdate.url",null);
       }
       if(selections.length==1){
         apps.$set("cmdbs.cdnupdate.url","cmdb/cdn/"+selections[0]+"/update/");
       }
     });
     it.on('all.bs.table', function (e, name, args) {
       
     });
   // }
   setTimeout(function () {
       // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
       //   var that = $(this);
       //   that.parent().toggleClass('open');
       //   $(document).mousedown(function(event){
       //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
       //       that.parent().removeClass('open');
       //     }
       //   })
       // });
   }, 200);

   function getIdSelections(it) {
       return $.map(it.bootstrapTable('getSelections'), function (row) {
           return row.uuid
       });
   }
   function getHeight(it) {
       return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
   }
    $("#cdnsearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/cdns?search="+val});
      }
    })
  }
  function loadcontract(url){
    var it = $("#contract_table");
   // loadcmd(it,url)

   // var getupdatecmd = {
   //   'click .btn':function(e, value, row, index){
   //     console.log(e.target.id.split("_")[1])
   //     tabss[app].$set("platcreateurls.updatecmd",row.url);
   //     tabss[app].showp(e,e.target.id.split("_")[1]);
   //   }
   // }
   $("#appmodalcontractupdate").css("position","relative").appendTo($("body"));
   apps.targetcmdb["contractupdate"] = $("#appmodalcontractupdate").find(".modal-dialog");
   apps.$set("cmdbs.contractupdate.name","更新合同");
   $("#appmodalcontractupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
   $("#appmodalcontractupdate").wsdraggable({handle:'.modal-header'});
   $("#appmodalcontractcreate").css("position","relative").appendTo($("body"));
   apps.targetcmdb["contractcreate"] = $("#appmodalcontractcreate").find(".modal-dialog");
   apps.$set("cmdbs.contractcreate.name","创建合同");
   apps.$set("cmdbs.contractcreate.url","cmdb/contract/create/");
   $("#appmodalcontractcreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
   $("#appmodalcontractcreate").wsdraggable({handle:'.modal-header'});
     it.bootstrapTable('destroy');
     it.bootstrapTable({
       sidePagination:"server",
       url:url,
       queryParams:queryParams,
       responseHandler:responseHandler,
       columns: [{
           field: 'state',
           checkbox: true,
           align: 'center',
           valign: 'middle'
       },{
           field: 'name',
           title: '合同名称',
           sortable: true,
           searchable:true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'number',
           title: '合同编号',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'created_at',
           title: '创建时间',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }, {
           field: 'expire_date',
           title: '过期时间',
           searchable:true,
           sortable: true,
           // footerFormatter: totalNameFormatter,
           align: 'center'
       }],
     });
     it.on('check.bs.table uncheck.bs.table ' +
           'check-all.bs.table uncheck-all.bs.table', function () {
       selections = getIdSelections(it);
       if(selections.length==0){
         apps.$set("cmdbs.contractupdate.url",null);
       }
       if(selections.length>1){
         apps.$set("cmdbs.contractupdate.url",null);
       }
       if(selections.length==1){
         apps.$set("cmdbs.contractupdate.url","cmdb/contract/"+selections[0]+"/update/");
       }
     });
     it.on('all.bs.table', function (e, name, args) {
       
     });
   // }
   setTimeout(function () {
       // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
       //   var that = $(this);
       //   that.parent().toggleClass('open');
       //   $(document).mousedown(function(event){
       //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
       //       that.parent().removeClass('open');
       //     }
       //   })
       // });
   }, 200);

   function getIdSelections(it) {
       return $.map(it.bootstrapTable('getSelections'), function (row) {
           return row.uuid
       });
   }
   function getHeight(it) {
       return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
   }
    $("#contractsearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/contracts?search="+val});
      }
    })
  }
  function locacmdbdashboard(url){

    $.ajax({
      url:"/api/"+localStorage.getItem("cmdbid")+"/widgets",
      type:"get",
      dataType:"json",
      success:function(data){
        apps.$set("widget",data.results);
      }
    })
    $.ajax({
      url:"/api/users/"+localStorage.getItem("cmdbid")+"/widgets",
      type:"get",
      dataType:"json",
      success:function(data){
        apps.$set("widgetSelected",data.results);
        var yuzhi = data.results;
        var block = [],pie=[],line=[],column=[];
        for(var i =0;i<yuzhi.length;i++){
          $.ajax({
            url:yuzhi[i].url,
            type:"get",
            dataType:"json",
            success:function(data){
              if(data.kind == "block"){
                block.push(data);
              }
              if(data.kind == "pie"){
                pie.push(data);
              }
              if(data.kind == "line"){
                line.push(data);
              }
              if(data.kind == "column"){
                column.push(data);
              }
            }
          })
        }

        apps.$set("block",block);
        apps.$set("pie",pie);
        apps.$set("line",line);
        apps.$set("column",column);
        apps.$watch("pie",function(pie){
            for(var i=0;i<pie.length;i++){
              $("#"+pie[i].kind+"_charts"+i).highcharts({
                  chart: {
                      plotBackgroundColor: null,
                      plotBorderWidth: null,
                      plotShadow: false
                  },
                  credits: {
                      text: '',
                      href: ''
                  },
                  title: {
                      text:""
                  },
                  tooltip: {
                    pointFormat: '{series.name}: <b>{point.percentage:.1f}%</b>'
                  },
                  plotOptions: {
                      pie: {
                          allowPointSelect: true,
                          cursor: 'pointer',
                          dataLabels: {
                              enabled: true,
                              color: '#000000',
                              connectorColor: '#000000',
                              format: ''
                          }
                      }
                  },
                  series: [{
                      type: 'pie',
                      name: '',
                      data: pie[i].series
                  }]
              });
            }
        });
        var id = window.localStorage.getItem("cmdbid");
        // console.log(id)
        $("#addchart form input[type='button']").unbind("click").click(function(){
          // console.log("aasdfasdf")
          var form = $(this).parents("form");
          $.ajax({
            url:"api/users/widgets/create",
            type:"post",
            dataType:"json",
            data:{
              widget_id:form.find("select").val(),
              appid:id
            },
            success:function(data){
              if(data.success){
                apps.$set("addchart",false);
                locacmdbdashboard(url);
              }
            }
          })
        })//users/widgets/create/
      }
    })
  }

  function loaddomain(url){
    var it = $("#domain_table");
    // loadcmd(it,url)

    // var getupdatecmd = {
    //   'click .btn':function(e, value, row, index){
    //     console.log(e.target.id.split("_")[1])
    //     tabss[app].$set("platcreateurls.updatecmd",row.url);
    //     tabss[app].showp(e,e.target.id.split("_")[1]);
    //   }
    // }
    $("#appmodaldomainupdate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["domainupdate"] = $("#appmodaldomainupdate").find(".modal-dialog");
    apps.$set("cmdbs.domainupdate.name","更新合同");
    $("#appmodaldomainupdate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodaldomainupdate").wsdraggable({handle:'.modal-header'});
    $("#appmodaldomaincreate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["domaincreate"] = $("#appmodaldomaincreate").find(".modal-dialog");
    apps.$set("cmdbs.domaincreate.name","创建合同");
    apps.$set("cmdbs.domaincreate.url","cmdb/domain/create/");
    $("#appmodaldomaincreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodaldomaincreate").wsdraggable({handle:'.modal-header'});
      it.bootstrapTable('destroy');
      it.bootstrapTable({
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        columns: [{
            field: 'state',
            checkbox: true,
            align: 'center',
            valign: 'middle'
        },{
            field: 'domain',
            title: '域名',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'ipc_ip',
            title: 'IP',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'ipc_id',
            title: '备案号',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'ipc_name',
            title: '主体',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'created_at',
            title: '创建时间',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'expire_date',
            title: '过期时间',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }],
      });
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
        apps.$set("selectedidc",selections);
        if(selections.length==0){
          apps.$set("cmdbs.domainupdate.url",null);
          apps.$set("cmdbs.domaindelete",false);
        }
        if(selections.length>1){
          apps.$set("cmdbs.domainupdate.url",null);
          apps.$set("cmdbs.domaindelete",false);
        }
        if(selections.length==1){
          apps.$set("cmdbs.domainupdate.url","cmdb/domain/"+selections[0]+"/update/");
          apps.$set("cmdbs.domaindelete",true);
        }
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
    // }
    setTimeout(function () {
        // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
        //   var that = $(this);
        //   that.parent().toggleClass('open');
        //   $(document).mousedown(function(event){
        //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
        //       that.parent().removeClass('open');
        //     }
        //   })
        // });
    }, 200);

    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }

    $("#resolvesearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/resolvers?search="+val});
      }
    })
  }

  function loadresolve(url){
    var it = $("#resolve_table");
    // loadcmd(it,url)

    // var getupdatecmd = {
    //   'click .btn':function(e, value, row, index){
    //     console.log(e.target.id.split("_")[1])
    //     tabss[app].$set("platcreateurls.updatecmd",row.url);
    //     tabss[app].showp(e,e.target.id.split("_")[1]);
    //   }
    // }
    $("#appmodalresolvecreate").css("position","relative").appendTo($("body"));
    apps.targetcmdb["resolvecreate"] = $("#appmodalresolvecreate").find(".modal-dialog");
    apps.$set("cmdbs.resolvecreate.name","创建解析");
    apps.$set("cmdbs.resolvecreate.url","cmdb/resolver/create/");
    $("#appmodalresolvecreate").find(".modal-dialog").addClass("dialog-init").wsresizable();
    $("#appmodalresolvecreate").wsdraggable({handle:'.modal-header'});
      it.bootstrapTable('destroy');
      it.bootstrapTable({
        sidePagination:"server",
        url:url,
        queryParams:queryParams,
        responseHandler:responseHandler,
        columns: [
        // {
        //     field: 'state',
        //     checkbox: true,
        //     align: 'center',
        //     valign: 'middle'
        // },
        {
            field: 'record',
            title: '域名',
            sortable: true,
            searchable:true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'description',
            title: '详情',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'username',
            title: '操作人',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }, {
            field: 'created_at',
            title: '操作时间',
            searchable:true,
            sortable: true,
            // footerFormatter: totalNameFormatter,
            align: 'center'
        }],
      });
      it.on('check.bs.table uncheck.bs.table ' +
            'check-all.bs.table uncheck-all.bs.table', function () {
        selections = getIdSelections(it);
      });
      it.on('all.bs.table', function (e, name, args) {
        
      });
    // }
    setTimeout(function () {
        // $(".bootstrap-table,.project-filter,.page-list").delegate(".dropdown-toggle","click",function(){
        //   var that = $(this);
        //   that.parent().toggleClass('open');
        //   $(document).mousedown(function(event){
        //     if($(event.target).parents(".bootstrap-table").length==0&&$(event.target).parents(".project-filter").length==0){
        //       that.parent().removeClass('open');
        //     }
        //   })
        // });
    }, 200);

    function getIdSelections(it) {
        return $.map(it.bootstrapTable('getSelections'), function (row) {
            return row.uuid
        });
    }
    function getHeight(it) {
        return it.parents(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop - 110;
    }
    $("#domainsearch").unbind("keyup").keyup(function(e){
      var val = $(this).val();
      if(val==""){
        it.bootstrapTable("refresh",{url:url});
      }
      if(e.keyCode==13){
        it.bootstrapTable("refresh",{url:"/api/search/domains?search="+val});
      }
    })
  }
