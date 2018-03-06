/*所有table分页都会用到的两个方法*/
function queryParams(params){
  var data = {
    page_size:params.limit,
    page:parseInt(params.offset/params.limit)+1,
  }
  if(params.sort){
    data["ordering"] = (params.order=="desc"?"-":"")+params.sort;
  }
  return data;
}
function responseHandler(res) {
    var temp = {};
    temp["total"] = res.count;
    temp["rows"] = res.results;
    res = temp;
    return res;
}
function sorter(a,b){
    return a.localeCompare(b);
}

/**
 * 时间转换方法
 * @param {[type]} strTime [description]
 */
var transitionEnd = 'webkitAnimationEnd mozAnimationEnd MSAnimationEnd oAnimationEnd oanimationend animationend';
var desks; 
window.Interface = {
  FormatDate:function(strTime){
    var date = new Date(strTime);
    return date.getFullYear()+"-"+((date.getMonth()+1)<10?("0"+(date.getMonth()+1)):(date.getMonth()+1))+"-"+date.getDate();
  },
  // oneAnimationEnd:function(el,callback){
  // //动画执行完毕后要执行的事件，适用于只执行一次动画的场景，并且不影响其他功能的情况下使用
  // //以及使用其他方法代替setTimeout方法 避免内存消耗
  //     el.one('webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend', function(){
  //       callback(el)
  //     });
  // },
  setCookie:function(name,value,d){
    var Days = d||30;
    var exp = new Date();
    exp.setTime(exp.getTime() + Days*24*60*60*1000);
    document.cookie = name + "="+ escape (value) + ";expires=" + exp.toGMTString()+";path=/;";
  },
  //读取cookies
  getCookie:function(name){
    var arr,reg=new RegExp("(^| )"+name+"=([^;]*)(;|$)");
    if(arr=document.cookie.match(reg)) return unescape(arr[2]);
    else return null;
  },
  //删除cookies
  delCookie:function(name){
    var exp = new Date();
    exp.setTime(exp.getTime() - 1);
    var cval=this.getCookie(name);
    if(cval!=null) document.cookie= name + "="+cval+";expires="+exp.toGMTString()+";path=/;";
  } 

}
//设置全局table可排序
// $.extend($.fn.bootstrapTable.columnDefaults, {
//     sortable: true
// });
window.GCR = {
    init:function(){
      this.loadBg();
      //this.setip();
      this.baseHandle();
      this.fishdock();
    },
    loadBg:function(){
      var app = $("#app"),
          bg = window.localStorage.getItem("current-bg-url")&&window.localStorage.getItem("current-bg-url").replace("app/","")||'{{STATIC_URL}}images/background/background.jpg',
          cssbg = window.localStorage.getItem("current-bg-url")?window.localStorage.getItem("current-bg-url").replace("app/",""):'{{STATIC_URL}}images/background/background.jpg';
      app.css("background","url('"+bg+"') 50% / cover fixed");

      var pseheader = this.ruleSelector(".header::before").slice(-1),
          pselogin = this.ruleSelector("#login::before").slice(-1),
          pseside = this.ruleSelector(".sidebar::before").slice(-1);
      pseheader[0].style.background = "url('"+cssbg+"') 50% / cover fixed";
      pselogin[0].style.background = "url('"+cssbg+"') 50% / cover fixed";
      pseside[0].style.background = "url('"+cssbg+"') 50% / cover fixed";
    },
    setip:function(){
      var ele = document.getElementById("current_ip");
      ele.innerHTML = returnCitySN["cname"]+" "+returnCitySN["cip"];
    },
    baseHandle:function(){
      var _this = this;
      var rightkeymenu = $("#rightkey");
          ci_item = $("#app .bottom_tip .ci_item"),
          arrows_left = $("#app .containers .arrows_left"),
          arrows_right = $("#app .containers .arrows_right"),
          citems = $("#applications .container_item"),
          current_con = $("#app .bottom_tip .current_con"),
          contaniers = $("#app .containers");

      // $("#modaltest").click(function(){
      //   event.stopPropagation();
      //   // $("#myModal").modal({backdrop: 'static'});
      //   rightkeymenu.removeClass('open');
      // })
      /**
      *顶部标签切换
      **/
      // ci_item.click(function(){
      //      var idx = $(this).index();
      //     _this.switchpage(idx);
      // })
      /**
      *向左侧滑动按钮
      **/
      arrows_left.click(function(){
        var index = desks.currentpage-1;
        if((index-1)>-1){
          _this.switchpage(index-1);
        }
      })
      /**
      *向右侧滑动按钮
      **/
      arrows_right.click(function(){
        var index = desks.currentpage-1;
        if((index+1)<desks.apps.length){
          _this.switchpage(index+1);
        }
      })

      /**
      *改变窗口大小时，动态更改左边距和dock栏的位置，做适应
      **/
      $(window).resize(function(){
          var index = $("#desktop .current_con").index();
          var box = $("#app .containers .container_items"),
          w = $("#app .containers")[0].offsetWidth;
          box.css({"margin-left":"-"+w*index+"px"})
          _this.fishdock();

          function getheight(it){
            return it.parents(".modal-body")[0].offsetHeight - it[0].offsetTop - 100;
          }
          var app = localStorage.getItem("currentapp");
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
      })

      /**
      *鼠标在页面左侧时，显示向左滑动按钮，反之显示向右滑动按钮
      **/
      $("#app").mousemove(function(e){
        if(e.pageX<500){
          arrows_left.css("display","block");
        }else{
          arrows_left.css("display","none");
        }

        if(e.pageX>contaniers[0].offsetWidth-500){
          arrows_right.css("display","block");
        }else{
          arrows_right.css("display","none");
        }
      })


      /*
      禁用右键
       */
      document.oncontextmenu=function(){//屏蔽浏览器右键事件
        return false;
      };
      var isIE = navigator.appName;
      //判断是否是IE浏览器
      //添加右击事件
      $("#app").bind("mousedown",function (event){
        // rightkeymenu.removeClass('open')
        if(event.which==3&&$(event.target).parents(".app").length==0&&!$(event.target).hasClass('app')){
           rightkeymenu.css("top",event.pageY-20).css("left",event.pageX).addClass("open");
        }
        if(event.which ==1){
          rightkeymenu.removeClass("open");
        }

      });

    },
    fishdock:function(){
        // $(document).ready(function(){
        setTimeout(function(){
          var sidebar = $("#dock");
          sidebar.css({
            marginLeft:($("body")[0].clientWidth-sidebar[0].clientWidth)/2
          })
          $('#dock').Fisheye({
            maxWidth: 35,
            items: 'li',
            // itemsText: 'span',
            container: '.centerd',
            itemWidth: 40,
            proximity: 100,
            halign : 'center'
          })
        },0)
    },
    ruleSelector:function(selector){
      /**
       * 获取伪类的方法
       * @param  {[type]} selector [description]
       * @return {[type]}          [description]
       */
      function uni(selector) {
        return selector&&selector.replace(/::/g, ':')
      }
      return Array.prototype.filter.call(Array.prototype.concat.apply([], Array.prototype.map.call(document.styleSheets, function(x) {
        return Array.prototype.slice.call(x.cssRules);
      })), function(x) {
        return uni(x.selectorText) === uni(selector);
      });
    },
    switchpage:function(idx){
      /**
      *切换页面
      **/
      var box = $("#app .containers .container_items"),
      w = $("#app .containers")[0].offsetWidth;
      if(parseInt(box.css("margin-left"))!=w*idx){
        box.css({"margin-left":"-"+w*idx+"px"})
        desks.currentpage = idx+1;
      }
      // $("#app .bottom_tip .current_con").removeClass('current_con');
      // $("#app .bottom_tip .ci_item").eq(idx).addClass('current_con');
    },
    modals:{
      ready:function(){
        $("body .modal .modal-dialog").addClass("dialog-init").wsresizable();
        $("body .modal").wsdraggable({handle:'.modal-header'});
      },
      show:function(it,intr){
        // console.log(it)
        var length = $(".modal.in").length;
        // modals.each(function(i,ele){
        var v = length*10;
        it.find(".modal-dialog").css("margin",v+"px "+"0px 0px "+v+"px");
        // })
        $("#rightkey").removeClass('open');
        var w = $(window).width()/2>600?$(window).width()/2:600;
        var h = $(window).height()/2>400?$(window).height()/2:400
        var l = ($(window).width()-w)/2,
        t = ($(window).height()-h)/2;
        // if(it.find(".modal-dialog")[0].offsetWidth==0){
          it.find(".modal-dialog").css({
            left:l+"px",
            top:t+"px",
            width:w,
            height:h
          })
          it.find(".modal-dialog .modal-content").css({
            height:h
          })
          it.addClass('animated');
          if(intr){
            it.find(".modal-dialog").css("display","none");
          }else{
            it.find(".modal-dialog").css("display","block");
          }
        // }
      },
      hide:function(){
        it = false;
      },
      max:function(flag,el,initval,key){
        flag?el.parents(".modal").addClass('maxmodal'):el.parents(".modal").removeClass("maxmodal");
        el.parents(".modal").removeClass("slideInUp");
        function getheight(it){
          return el.find(".modal-body")[0].offsetHeight - it.parents(".fixed-table-container")[0].offsetTop-110;
        }
        var $table = el.find(".fixed-table-body table");
        setTimeout(function(){
          $table.each(function(){
            var _that = $(this);
            _that.bootstrapTable('resetView', {
                height: getheight(_that)
            });
            
          })   
        },300)
         
      },
      min:function(el){
        function getheight(it){
          return it.parents(".modal-body")[0].offsetHeight - it[0].offsetTop - 50;
        }
        var $table = el.find(".fixed-table-body table");
        $table.each(function(){
          var _that = $(this);
          if(_that.bootstrapTable){
            _that.bootstrapTable('resetView', {
                height: getheight(_that)
            });
          }
          
        }) 
      }
    }
};
GCR.init();
/**
*注册modal组件
**/
Vue.config.delimiters = ['<%', '%>'];
var modals = ["modal","tooltip","dropdown","tabset","tab","alert","vSelect","vOption","datepicker"];
var vmodal = ["modal","tooltip","dropdown","tabset","tab","alert","select","option","datepicker"];

for(var i=0;i<modals.length;i++){
  Vue.component(modals[i],VueStrap[vmodal[i]]);
}


// for(var v in VueStrap){
//   console.log(v,VueStrap[v])
//   Vue.component(v,VueStrap[v]);
// }
var zindex = 0;

/**
*是否登录
**/
var islogin = Interface.getCookie("logininfo")?true:false;


/**
退出登录
**/
var logout = new Vue({
  el:"#logout",
  data:function(){
    return {
      time:Interface.FormatDate(new Date())
    }
  }
})

/**
*实例化用户下拉框
**/

startmenu = new Vue({
  el:"#usetting",
  data:function(){
    var all = {{desktop.menutoJSON|safe}},pages = [],zooms={},ismax={},name={},url={},datatype={};
    // console.log(all)
    for(var k in all){
      pages.push(k);
      zooms[k] = all[k].zooms;
      ismax[k] = all[k].ismax;
      name[k] = all[k].name;
      datatype[k] = all[k].ct;
      if(k!="users"){
        url[k] = all[k].url;
      }else{
        url[k] = "/api/users";
      }
      
    }

    zooms["adduser"] = false;
    ismax["adduser"] = false;
    name["adduser"] = "添加用户";
    zooms["addapp"] = false;
    ismax["addapp"] = false;
    name["addapp"] = "添加应用";
    zooms["addnode"] = false;
    ismax["addnode"] = false;
    name["addnode"] = "添加节点";
    return {
      search:"",
      pages:pages,
      zooms:zooms,
      ismax:ismax,
      name:name,
      datatype:datatype,
      url:url,
      init_val:{},
      removebtn:{},
      selecteds:{},
      deleteurl:{
        "user":"/api/users/delete",
        "app":"/api/apps/delete",
        "plat":"/api/platforms/delete"
      }
    }
  },
  ready:function(){
    this.target = {};
    this.jsondata = {};
    for(var i =0;i<this.pages.length;i++){
      // var frame = $("<iframe frameborder=0 scrolling=0 width=100% height=100% name='startiframe_"+this.pages[i]+"'>");
      // $("#"+this.pages[i]+"_manage").find(".modal-body").html(frame);
      this.target[this.pages[i]] = $("#"+this.pages[i]+"_manage")
    }
    for(var t in this.target){
      this.target[t].appendTo($("body"));
    }
    var temp = ["adduser","addplat","addapp","addnode"]
    for(var i=0;i<temp.length;i++){
      this.target[temp[i]] = $("#"+temp[i]+"_manage");
      this.target[temp[i]].appendTo($("body"));
    }
    GCR.modals.ready();
  },
  methods:{
    show:function(event,key,intro){
      event?event.stopPropagation():null;
      var tstr = "#"+key+"_manage";
      var _this = this;
      if(this.zooms[key]){
        $("#desktop").find("li[data-target='"+key+"_manage']").addClass('flop').one(transitionEnd,function(){
          $(this).removeClass('flop');
          desks.toggleMin(event,key+"_manage",true);
        });
        return false;
      }
      this.zooms[key] = true;
      zindex++;
      $(tstr).addClass('in');
      $(tstr).find(".modal-dialog").css("z-index",zindex);
      GCR.modals.show($(tstr),intro);
      if(key=="adduser"){
        // console.log(key)
        $.ajax({
            url:"/users/create",
            type:"get",
            dataType:"html",
            success:function(html){
                $(tstr).find(".modal-body").html(html);
            }
        })
      }else if(key=="addapp"){
        $.ajax({
            url:"/ops/apps/create",
            type:"get",
            dataType:"html",
            success:function(html){
                $(tstr).find(".modal-body").html(html);
            }
        })
      }else if(key=="addnode"){
        $.ajax({
            url:"/ops/nodes/create",
            type:"get",
            dataType:"html",
            success:function(html){
                $(tstr).find(".modal-body").html(html);
            }
        })
      }else if(key=="addplat"){
        $.ajax({
            url:"/ops/plat/create",
            type:"get",
            dataType:"html",
            success:function(html){
                $(tstr).find(".modal-body").html(html);
            }
        })
      }else{
        var noreq = ["users","roles","apps","platforms"];
        $.ajax({
            url:_this.url[key],
            type:"get",
            dataType:_this.datatype[key],
            success:function(html){
              if(_this.datatype[key]=="html"){
               $(tstr).find(".modal-body").html(html);
              }
            }
        })
      }
    },
    close:function(event,key,p){
      event.stopPropagation();
      var tstr = "#"+key+"_manage";
      !p?this.zooms[key] = false:null;
      !p?zindex--:null;
      $(tstr).find(".modal-dialog").css("z-index","");
      $(tstr).removeClass('maxmodal');
      if(p){
        $(tstr).removeClass('slideInUp').addClass("zoomOutDown").one(transitionEnd,function(){
          if($(this).hasClass("zoomOutDown")){
            $(this).removeClass('in');
          }
        });
      }else{
        $(tstr).removeClass('in');
      }
    },
    min:function(event,key){
      event.stopPropagation();
      var tstr = "#"+key+"_manage";
      this.close(event,key,"animate");//与关闭操作相同，并加入到desktop最小化列表中
      var name = this.name[key];
      var icon ='{{STATIC_URL}}images/desktop-icons/settings.png';
      if(key=="users")icon ='{{STATIC_URL}}images/desktop-icons/users.png';
      if(key=="roles")icon ='{{STATIC_URL}}images/desktop-icons/roles.png';
      if(key=="apps")icon ='{{STATIC_URL}}images/desktop-icons/apps.png';
      desks.minifys.push({
        el:$(tstr),
        target:key+"_manage",
        index:key,
        // show:false,
        name:name,
        icon:icon,
      });
      desks.isflop.push(false);
      GCR.fishdock();
      GCR.modals.min(this.target[key]);
    },
    max:function(event,key){
      event.stopPropagation();
      this.ismax[key] = !this.ismax[key];
      var _target = this.target[key].find(".modal-dialog")[0];
      if(this.ismax[key]){//经过上述转换以后说明ismax是放大时候的状态，因此，要记录原始的width height left top等
        this.init_val[key] = {
          left:_target.offsetLeft,
          top:_target.offsetTop,
          width:_target.offsetWidth,
          height:_target.offsetHeight
        }
      }
      GCR.modals.max(this.ismax[key],this.target[key].find(".modal-dialog"),this.init_val[key],key);
      
    },
    removesm:function(type){
      var _t = this;
      if(confirm("确定要删除选中数据吗？")){
        $.ajax({
          url:_t.deleteurl[type],
          type:"post",
          dataType:"json",
          data:{uuids:_t.selecteds[type].join(",")},
          success:function(datas){
            if(datas.success){
              toastr.success(datas.msg,datas.success?"成功":"失败");
            }else{
              toastr.error(datas.msg,datas.success?"成功":"失败");
            }
            
          }
        })
      }
      
    }
  }
})


/**
*实例化通知组件
**/
var alerts = new Vue({
  el:"#alerts",
  data:function(){
    return {
      showTop:false,
      type:'success',
      label:{
        'success':'成功',
        'info':'提示',
        'danger':'危险',
        'warning':'警告'
      },
      content:''
    }
  }
})

/**
*实例化socket通知组件
**/
var winnotify = new Vue({
  el:"#notifyhandle",
  data:function(){
    return {
      seartext:'',
      message:[],
      show:false
    }
  }
})

/**
**实例化服务器以及区服树右键菜单
**/
var treeright = new Vue({
  el:"#treeright",
  data:function(){
    return {
      zoomModal:{'createpgroup':false,'updatepgroup':false},
      ismax:{'createpgroup':false,'updatepgroup':false},
      init_val:{},
      currenttree:{},
      appid:"",
      groupid:"",
      treeurl:""
    }
  },
  ready:function(){
    var _this = this;
    this["target"] = {"createpgroup":$("#createpgroupmodal").find(".modal-dialog"),"updatepgroup":$("#updatepgroupmodal").find(".modal-dialog")};
    this["target"]["createpgroup"].parent(".modal").appendTo($("body"));
    this["target"]["updatepgroup"].parent(".modal").appendTo($("body"));
    GCR.modals.ready();
  },
  methods:{
    show:function(event,key){
      event?event.stopPropagation():null;
      var target = key+"modal";
      if(this.zoomModal[key]){
        var _this = this;
        $("#desktop").find("li[data-target='"+target+"']").addClass('flop').one(transitionEnd,function(){
          $(this).removeClass('flop');
          _this.zoomModal = true;
          desks.toggleMin(event,target,true);
        });
        $("#treeright").removeClass('open');
        return false;
      } 
      this.zoomModal[key] = true;
      zindex++;
      $("#"+target).addClass('in');
      $("#"+target+" .modal-dialog").css("z-index",zindex+25+1050);
      if(this.currenttree.parents(".modal-dialog").css("position")=="fixed"){
        $("#"+target+" .modal-dialog").css("position","fixed");
      }
      $("#treeright").removeClass('open');
      GCR.modals.show($("#"+target));
      if(key=="createpgroup"){
        $.ajax({
          url:"/ops/platgroup/"+this.appid+"/create",
          type:"get",
          dataType:"html",
          success:function(html){
              $("#"+target).find(".modal-body").html(html);
          }
        })
      }else if(key=="updatepgroup"){
        $.ajax({
          url:"/ops/platgroup/"+this.groupid+"/update",
          type:"get",
          dataType:"html",
          success:function(html){
              $("#"+target).find(".modal-body").html(html);
          }
        })
      }
    },
    close:function(event,key,p){
      event.stopPropagation();
      var target = key+"modal";
      if(!p||p!="animate"){
        this.zoomModal[key]=false;
        zindex--;
      }
      $("#"+target+" .modal-dialog").css("z-index","");
      $("#"+target).removeClass('maxmodal');
      if(p&&p=="animate"){
        $("#"+target).removeClass('slideInUp').addClass("zoomOutDown").one(transitionEnd,function(){
          if($(this).hasClass("zoomOutDown")){
            $(this).removeClass('in');
          }
        });
      }else{
        $("#"+target).removeClass('in');
      }
    },
    min:function(event,key){
      event.stopPropagation();
      var target = key+"modal";
      this.close(event,key,"animate");//与关闭操作相同，并加入到desktop最小化列表中
      desks.minifys.push({
        el:$("#"+target),
        target:target,
        // show:false,
        name:$("#"+target).find(".modal-title").text(),
        icon:'{{STATIC_URL}}images/desktop-icons/folder-document.png'
      });
      desks.isflop.push(false);
      GCR.fishdock();
    },
    max:function(event,key){
      event.stopPropagation();
      var target = key+"modal";
      this.ismax[key] = !this.ismax[key];
      if(this.ismax[key]){//经过上述转换以后说明ismax是放大时候的状态，因此，要记录原始的width height left top等
        this.init_val[key] = {
          left:target[0].offsetLeft,
          top:target[0].offsetTop,
          width:target[0].offsetWidth,
          height:target[0].offsetHeight
        }
      }
      GCR.modals.max(this.ismax[key],this.target[key],this.init_val[key]);
    },
  }  
})

/**
**实例化右键菜单modal
**/
var rkmodal = new Vue({
  el:"#rightkey",
  data:function(){
    return {
      list:["back","createtab"],
      zoomModal:{"back":false,"createtab":false},
      ismax:{"back":false,"createtab":false},
      init_val:{
      },
      //关于背景的一些data
      bg:{
        imgs:["{{STATIC_URL}}images/background/background.jpg",
              "{{STATIC_URL}}images/background/background-1.jpg",
              "{{STATIC_URL}}images/background/background-2.jpg",
              "{{STATIC_URL}}images/background/background-3.jpg",
              "{{STATIC_URL}}images/background/background-4.jpg",
              "{{STATIC_URL}}images/background/background-5.jpg",
              "{{STATIC_URL}}images/background/background-6.jpg",
              "{{STATIC_URL}}images/background/background-7.jpg",
              "{{STATIC_URL}}images/background/background-8.jpg",
              "{{STATIC_URL}}images/background/background-9.jpg",
              "{{STATIC_URL}}images/background/background-10.jpg"],
        selected:0
      }
    }
  },
  ready:function(){
    var _this = this;
    this["target"] = {};
    for(var i=0;i<_this.list.length;i++){
      this["target"][_this.list[i]] = $("#"+_this.list[i]+"_rightkey").find(".modal-dialog");
      this["target"][_this.list[i]].parent(".modal").appendTo($("body"))
    }
    GCR.modals.ready();
    if(window.localStorage.getItem("current-bg-url")){
      this.bg.selected = this.bg.imgs.indexOf(window.localStorage.getItem("current-bg-url"));
    }
  },
  methods:{
    show:function(event,key,url){
      event?event.stopPropagation():null;
      var target = key+"_rightkey";
      if(this.zoomModal[key]){
        var _this = this;
        $("#desktop").find("li[data-target='"+target+"']").addClass('flop').one(transitionEnd,function(){
          $(this).removeClass('flop');
          _this.zoomModal = true;
          desks.toggleMin(event,target,true);
        });
        $("#rightkey").removeClass('open');
        return false;
      } 
      this.zoomModal[key] = true;
      zindex++;
      $("#"+target).addClass('in');
      $("#"+target+" .modal-dialog").css("z-index",zindex);
      $("#rightkey").removeClass('open');
      GCR.modals.show($("#"+target));
      if(url){
        $.ajax({
          url:url,
          type:"get",
          dataType:"html",
          success:function(html){
              $("#"+target).find(".modal-body").html(html);
          }
        })
      }
    },
    close:function(event,key,p){
      event.stopPropagation();
      var target = key+"_rightkey";
      if(!p||p!="animate"){
        this.zoomModal[key]=false;
        zindex--;
      }
      $("#"+target+" .modal-dialog").css("z-index","");
      $("#"+target).removeClass('maxmodal');
      if(p&&p=="animate"){
        $("#"+target).removeClass('slideInUp').addClass("zoomOutDown").one(transitionEnd,function(){
          if($(this).hasClass("zoomOutDown")){
            $(this).removeClass('in');
          }
        });
      }else{
        $("#"+target).removeClass('in');
      }
    },
    min:function(event,key){
      event.stopPropagation();
      var target = key+"_rightkey";
      this.close(event,key,"animate");//与关闭操作相同，并加入到desktop最小化列表中
      desks.minifys.push({
        el:$("#"+target),
        target:target,
        // show:false,
        name:$("#"+target).find(".modal-title").text(),
        icon:'{{STATIC_URL}}images/desktop-icons/folder-document.png'
      });
      desks.isflop.push(false);
      GCR.fishdock();
    },
    max:function(event,key){
      event.stopPropagation();
      var target = key+"_rightkey";
      this.ismax[key] = !this.ismax[key];
      if(this.ismax[key]){//经过上述转换以后说明ismax是放大时候的状态，因此，要记录原始的width height left top等
        this.init_val[key] = {
          left:target[0].offsetLeft,
          top:target[0].offsetTop,
          width:target[0].offsetWidth,
          height:target[0].offsetHeight
        }
      }
      GCR.modals.max(this.ismax[key],this.target[key],this.init_val[key]);
    },
    setbg:function(event,index){
      event.stopPropagation();
      this.bg.selected = index;
      var app = $("#app"),
          bg = this.bg.imgs[index],
          cssbg = this.bg.imgs[index].replace("app","..");
      app.css("background","url('"+bg+"') 50% / cover fixed");
      var pseheader = GCR.ruleSelector(".header::before").slice(-1),
          pselogin = GCR.ruleSelector("#login::before").slice(-1),
          pseside = GCR.ruleSelector(".sidebar::before").slice(-1);
      pseheader[0].style.background = "url('"+cssbg+"') 50% / cover fixed";
      pselogin[0].style.background = "url('"+cssbg+"') 50% / cover fixed";
      pseside[0].style.background = "url('"+cssbg+"') 50% / cover fixed";
      window.localStorage.setItem("current-bg-url", bg);
      alerts.$set('content', "修改桌面背景成功");
      alerts.$set('showTop',true);
    }
  }
})

rkmodal.$set("preimg",[]);//图片预加载，防止360浏览器切换背景时闪烁，但是貌似没什么卵用
for(i=0;i<rkmodal.bg.imgs.length;i++){
    var img = new Image();
    img.src = rkmodal.bg.imgs[i];
    img.onload = function(){
      this.width = 1920;
      this.height = 1200;
    }
    rkmodal["preimg"].push(img); 
}

/**
*实例化apps的modal
**/
var apps = new Vue({
  el:"#applications",
  data:function(){
    console.log("=========")
    console.log({{desktop.dock|safe}})
    console.log({{desktop.app|safe}})
    return {
      page:{{desktop.dock|safe}},
      apps:{{desktop.app|safe}},
      zooms:[],
      ismax:[],
      init_val:[],
      /*以下为ADD APP 按钮单独写的部分属性*/
      zoomadd:[],
      ismaxadd:[],
      init_valadd:{},
      appchild:{
        zoom:{},
        ismax:{},
        init_val:{},
        target:{}
      },
      //以下是关于cmdb的
      cmdbtab:[],
      cmdbselected:[],
      addchart:false,
      cmdbactive:"dashboard",
      widgets:[],
      widgetSelected:[],
      block:[],
      pie:[],
      line:[],
      column:[],
      cmdbs:{
        "cmdbupdate":{}
      },
      monitors:{},//monitor相关1,
      cmdbselectedtpl:[],//选中的cmdb已有的监控template
      cmdbselectedproxy:[],
      cmdbselectedgroup:[],
      monitorimg:[],
      monitortimezone:0,//时间差

      deletebtn:{},
      deleteurl:{
        "acce":"/api/accelerates/delete/",
        "cdn":"/api/cdns/delete",
        "hostdown":"/api/hosts/bulk/delete"
      },
      selectedde:{},
      entryshow:false,
      entryidcs:[],
      selectedidc:[]
    }
  },
  ready:function(){
    _this = this;
    for(var i=0;i<this.apps.length;i++){
        this.zooms.push(false);
        this.ismax.push(false);
    }
    for(var i =0;i<this.page.length;i++){
      this.zoomadd.push(false);
      this.ismaxadd.push(false);
    }
    this['targetcmdb'] = {};
    this['target'] = [];
    this['targetadd'] = [];
    var apps = this.apps;
    // console.log(apps)
    for(var i=0;i<apps.length;i++){
      // var frame = $("<iframe frameborder='0' scrolling='0' width='100%' height='100%' name='appiframe_"+i+"'></iframe>");
      // $("#appmodal"+i).find(".modal-body").html(frame);
      $("#appmodal"+i).appendTo($("body"));
      this.target[i] = $("#appmodal"+i).find(".modal-dialog");
    }
    for(var i=0;i<this.page.length;i++){
      this.targetadd[i] = $("#appmodal999_"+(i+1)).find(".modal-dialog");
    }

    this.appchild.zoom["addplattogame"] = false;
    $("#addplattogame_manage").appendTo($("body"))
    this.appchild.target["addplattogame"] = $("#addplattogame_manage").find(".modal-dialog");

    GCR.modals.ready();
    $.ajax({
      url:"/api/idcs",
      type:"get",
      dataType:"json",
      success:function(datas){
        _this.$set("entryidcs",datas.results);
      }
    })
  },
  methods:{
    show:function(event,index,apid){
      var _this = this;
      event.stopPropagation();
      if(typeof index=="string"&&index.indexOf("999")>-1){
        var pid = $("#appmodal"+index).attr("data-pageid");
        // console.log(pid)
        var url = pid==0?"/thirdapps/create":"/ops/apps/create"
        $.ajax({
            url:url,
            type:"get",
            dataType:"html",
            success:function(html){
                $("#appmodal"+index).find(".modal-body").html(html);
                $("#appmodal"+index).appendTo($("body"));
            }
        })
        var pageid = parseInt(index.split("_")[1]);
        if(this.zoomadd[pageid-1]){
          $("#desktop").find("li[data-target='appmodal"+index+"']").addClass('flop').one(transitionEnd,function(){
              $(this).removeClass('flop');
              _this.zoomadd[pageid-1] = true;
              desks.toggleMin(event,"appmodal"+index,true);
          });
          return false;
        }
        this.zoomadd[pageid-1] = true;
        zindex++;
        $("#appmodal"+index).addClass('in');
        $("#appmodal"+index).find(".modal-dialog").css("z-index",zindex);
        GCR.modals.show($("#appmodal"+index));
        _this.max(event,index);
      }else{
        var _this = this;
        // console.log(_this.apps[index])
        //v-bind:href="item.url" v-bind:target="'appiframe_'+$index"
        if(_this.apps[index]&&_this.apps[index].appid){
          if(_this.apps[index].appid!="1"){
            $.ajax({
                url:_this.apps[index].url,
                type:"get",
                dataType:"html",
                success:function(html){
                  // console.log($("#appmodal"+index))
                  if($("#appmodal"+index).attr("data-pageid")=="0"){
                    if(html.indexOf("iframe")>-1){
                      $("#appmodal"+index).find(".modal-footer").remove();
                      $("#appmodal"+index).find(".modal-body").css("overflow","hidden").html(html);
                      $("#appmodal"+index).find(".modal-body").find("iframe").css("top",0);
                      $("#appmodal"+index).find(".modal-body").find("iframe")[0].src=$("#appmodal"+index).find(".modal-body").find("iframe").attr("data-src");
                    }else{
                      $("#appmodal"+index).find(".modal-body").html(html);
                    }
                    $("#appmodal"+index).appendTo($("body"));
                  }else{
                    $("#appmodal"+index).find(".modal-body").html(html);
                    $("#appmodal"+index).appendTo($("body"));
                    localStorage.setItem("currentapp","#appmodal"+index);
                    localStorage.setItem("currentappid",apid);
                    eval("("+loadtab("#appmodal"+index)+")");
                  }
                   
                    // $("#logdetail .logfirst,#logdetail .logtwo").html("");
                }
            })
          }else{
            eval("("+loadcmdb("#appmodal"+index,_this,apid)+")");
          }
        }else{
          // console.log(index)
          if(index!="addmonitor"&&index!="cmdbentry"){
            $.ajax({
                url:_this.cmdbs[index].url,
                type:"get",
                dataType:"html",
                success:function(html){
                    $("#appmodal"+index).find(".modal-body").html(html);
                }
            })
          }
          if(index=="cmdbentry"){
            $.ajax({
              url:"/cmdb/hosts/bulk/input/",
              type:"get",
              dataType:"html",
              success:function(html){
                $("#appmodal"+index).find("#duotai .padd").html(html);
              }
            });
            
            $.ajax({
              url:"/cmdb/hosts/create",
              type:"get",
              dataType:"html",
              success:function(html){
                $("#appmodal"+index).find("#shoudong .padd").html(html);
              }
            })
          }

        }
        if(this.zooms[index]){
          var _this = this;
          $("#desktop").find("li[data-target='appmodal"+index+"']").addClass('flop').one(transitionEnd,function(){
              $(this).removeClass('flop');
              desks.toggleMin(event,"appmodal"+index,true);
          });
          return false;
        }
        
        // console.log(this.zooms["cmdbupdate"])
        this.zooms[index] = true;
        zindex++;
        $("#appmodal"+index).addClass('in');
        $("#appmodal"+index).find(".modal-dialog").css("z-index",zindex+20);
        GCR.modals.show($("#appmodal"+index));
        if(!isNaN(parseInt(index))){
          _this.max(event,index);
        }
      }
    },
    close:function(event,index,p){
      event.stopPropagation();
      if(typeof index=="string"&&index.indexOf("999")>-1){
        var pageid = parseInt(index.split("_")[1])
        !p?this.zoomadd[pageid-1] = false:null;
      }else{
        !p?this.zooms[index] = false:null;
      }
      !p?zindex--:null;
      $("#appmodal"+index).find(".modal-dialog").css("z-index","");
      $("#appmodal"+index).removeClass('maxmodal');
      if(p){
        $("#appmodal"+index).removeClass('slideInUp').addClass("zoomOutDown").one(transitionEnd,function(){
          if($(this).hasClass("zoomOutDown")){
            $(this).removeClass('in');
          }
        });
      }else{
        $("#appmodal"+index).removeClass('in');
        $("#appmodal"+index).find(".modal-dialog").fadeOut();
      }
    },
    min:function(event,index){
      event.stopPropagation();
      this.close(event,index,"animate");//与关闭操作相同，并加入到desktop最小化列表中
      var name = typeof index=="string"&&index.indexOf("999")>-1?"增加项目":(isNaN(parseInt(index))?this.cmdbs[index].name:this.apps[index].name);
      var icon = typeof index=="string"&&index.indexOf("999")>-1?'{{STATIC_URL}}images/desktop-icons/folder-document.png':(isNaN(parseInt(index))?'{{STATIC_URL}}images/desktop-icons/folder-document.png':this.apps[index].icon);
      desks.minifys.push({
        el:$("#appmodal"+index),
        target:"appmodal"+index,
        index:index,
        // show:false,
        name:name,
        icon:icon,
      });
      desks.isflop.push(false);
      GCR.fishdock();
      if(typeof index=="string"&&index.indexOf("999")>-1){
        GCR.modals.min(this.target[index]);
      }else{
        GCR.modals.min(this.targetadd[index]); 
      }
    },
    max:function(event,index){
      event.stopPropagation();
      if(typeof index=="string"&&index.indexOf("999")>-1){
        // console.log(index)
        var pageid = parseInt(index.split("_")[1]);
        this.ismaxadd[pageid-1] = !this.ismaxadd[pageid-1];
        var _target = this.targetadd[pageid-1];
        if(this.ismaxadd[pageid-1]){//经过上述转换以后说明ismax是放大时候的状态，因此，要记录原始的width height left top等
          this.init_valadd[pageid-1] = {
            left:_target.offsetLeft,
            top:_target.offsetTop,
            width:_target.offsetWidth,
            height:_target.offsetHeight
          }
        }
        GCR.modals.max(this.ismaxadd[pageid-1],this.targetadd[pageid-1],this.init_valadd[pageid-1]);
      }else{
        this.ismax[index] = !this.ismax[index];
        // console.log(isNaN(parseInt(index)))
        var _target = isNaN(parseInt(index))?this.targetcmdb[index][0]:this.target[parseInt(index)][0];
        var targ = isNaN(parseInt(index))?this.targetcmdb[index]:this.target[parseInt(index)];
        if(this.ismax[index]&&!isNaN(parseInt(index))){//经过上述转换以后说明ismax是放大时候的状态，因此，要记录原始的width height left top等
          this.init_val[index] = {
            left:_target.offsetLeft,
            top:_target.offsetTop,
            width:_target.offsetWidth,
            height:_target.offsetHeight
          }
        }
        if(isNaN(parseInt(index))){
          GCR.modals.max(this.ismax[index],targ);
        }else{
          GCR.modals.max(this.ismax[index],targ,this.init_val[index]);
        }
        
      }
      
    },
    removecdn:function(type){
      var _t = this;
      if(confirm("确定要删除选中数据吗？")){
        $.ajax({
          url:_t.deleteurl[type],
          type:"post",
          dataType:"json",
          data:{uuids:type=="hostdown"?_t.cmdbselected.join(","):_t.selectedde[type].join(",")},
          success:function(datas){
            if(datas.success){
              toastr.success(datas.msg,datas.success?"成功":"失败");
            }else{
              toastr.error(datas.msg,datas.success?"成功":"失败");
            }
            
          }
        })
      }
    },
    deletedomain:function(){
      var _t = this;
      if(confirm("确定要删除选中数据吗？")){
        $.ajax({
          url:"/api/domains/"+_t.selectedidc[0]+"/delete/",
          type:"delete",
          dataType:"json",
          success:function(datas){
            if(datas.success){
              toastr.success(datas.msg,datas.success?"成功":"失败");
            }else{
              toastr.error(datas.msg,datas.success?"成功":"失败");
            }
            
          }
        })
      }
    },
    //cmdb 方法
    settimezone:function(event,num){
      this.monitortimezone = num;
    },

    entrybyidc:function(event,index,id){
      $(event.target).parents(".btn-group").removeClass('open');
      $.ajax({
        url:"/cmdb/hosts/"+id+"/input/",
        type:"get",
        dataType:"html",
        success:function(html){
          $("#appmodal"+index).find("#dantai .padd").html("<pre><code>"+html+"</code></pre>");
        }
      })
    }
  }
})

/**
*加载desktop列表
**/

desks = new Vue({
  el:"#desktop",
  data:function(){
    return {
      apps:{{desktop.dock|safe}},
      minifys:[],
      isflop:[],
      currentpage:1//数组个数与minifys相等
    }
  },
  ready:function(){

  },
  methods:{
    callswitchpage:function(idx){
      GCR.switchpage(idx);
    },
    toggleMin:function(event,item,trigger){
        event.stopPropagation();
        GCR.fishdock();
        var el = trigger?item:item.el;
        zindex++;
        if(trigger){
          for(var i=0;i<this.minifys.length;i++){
            if(this.minifys[i].target==item){
              this.minifys[i].el.css("z-index",zindex);
              this.minifys[i].el.addClass('in').addClass("slideInUp").removeClass("zoomOutDown")
              this.minifys.splice(i,1);
              this.isflop.splice(i,1);
              break;
            }
          }
        }else{
         item.el.css("z-index",zindex);
         item.el.addClass('in').addClass("slideInUp").removeClass("zoomOutDown");
         this.minifys.splice(this.minifys.indexOf(item),1);
         this.isflop.splice(this.minifys.indexOf(item),1)
        }
    }
  }
})


/**
*开始引导
**/
// $(document).ready(function(){
//   setTimeout(function(){
//     $("#usetting").find("button[data-toggle='dropdown']").click();
//     startmenu.show(null,'users',"intro");
//     startmenu.show(null,'adduser',"intro");
//     introJs().start().onchange(function(targetElement){
//       console.log(targetElement)
//       var step = parseInt($(targetElement).attr("data-step"));
//       if(step == 2){
//         $("#users_manage").find(".modal-dialog").css("display","block");
//       }else if(step==3){
//         $("#adduser_manage").find(".modal-dialog").css("display","block");
//       }
//       // return false;
//     }).onhintclick(function() {
//       alert("hint clicked");
//     });

//   },2000)
// })
//


/**
*form 提交方法处理
**/
$("body").delegate("form","submit",function(e){
  var t = $(this);
  if(t.attr("action")){
    e.preventDefault();
    // // var datas = t.serializeJson();
    // var datas = t.serialize();
    // console.log(datas)
    // return false;
    // // console.log(datas)
    // $.ajax({
    //   url:t.attr("action"),
    //   type:"post",
    //   dataType:"json",
    //   data:datas,
    //   success:function(data){
    //     t.parents(".modal").find(".close").click();
    //     toastr.success(data.msg,"成功");
    //   }
    // })
    var data = {};
    if(t.attr("action")=="/api/hosts/bulk/update"){
      data["uuids"] = apps.$get("cmdbselected").join(",");
    }
    t.ajaxSubmit({
        type:"post",
        dataType:"json",
        data:data,
        success: function(data) { // data 保存提交后返回的数据，一般为 json 数据
            t.parents(".modal").find(".close").click();
            if(data.success){
              toastr.success(data.msg,data.success?"成功":"失败");
              if(t.attr("action").indexOf("platgroup")>-1&&t.attr("action").indexOf("create")>-1){
                treeright.$get("currenttree").fancytree({url:treeright.$get("treeurl")});
              }
            }else{
              toastr.error(data.msg,data.success?"成功":"失败");
            }
            if(t.attr("action").indexOf("region/create")>-1){
                $.ajax({
                  url:"/api/"+localStorage.getItem("currentappid")+"/"+tabss[localStorage.getItem("currentapp")].platidfortab+"/regions/",
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
                    tabss[localStorage.getItem("currentapp")].$set("tabs",arr);
                  }
                })
            }
            if(t.attr("action").indexOf("execute")>-1){
              tabss[localStorage.getItem("currentapp")].$set("selectSrv",[]);
              $(localStorage.getItem("currentapp")).find("#srv-datas li").removeClass('srv-selected');
            }
            t.resetForm(); // 提交后重置表单
        }
       
    });
  }
}).delegate(".pagination-detail [data-toggle='dropdown']","click",function(){
  var that = $(this);
  $(this).parents(".btn-group").toggleClass("open");
  $(document).mousedown(function(event){
     if($(event.target).parents(".pagination-detail").length==0){
       that.parents(".btn-group").removeClass('open');
     }
   })
}).delegate(".columns-right [data-toggle='dropdown']", 'click', function(event) {
  var that = $(this);
    $(this).parents(".btn-group").toggleClass("open");
    $(document).mousedown(function(event){
       if($(event.target).parents(".columns-right").length==0){
         that.parents(".btn-group").removeClass('open');
       }
     })
}).delegate(".project-filter [data-toggle='dropdown']","click",function(){
  var that = $(this);
  $(this).parents(".btn-group").toggleClass("open");
  $(document).mousedown(function(event){
     if($(event.target).parents(".project-filter").length==0){
       that.parents(".btn-group").removeClass('open');
     }
   })
}).delegate(".modal[data-appid] .modal-dialog","click",function(e){
  e.stopPropagation();
  var t = $(this);
  localStorage.setItem("currentapp","#"+t.parents(".modal").attr("id"));
  localStorage.setItem("currentappid",t.parents(".modal").attr("data-appid"));
  // eval("("+loadtab("#"+t.parents(".modal").attr("id"))+")");
})

