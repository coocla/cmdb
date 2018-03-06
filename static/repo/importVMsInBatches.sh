#!/bin/bash
#author: coocla
#description: import server to surge and install surge agent. just so~ 

function validateRunAsRoot
{
  currentuser=`whoami`
  if [ "$currentuser" == "root" ];then
    echo `date "+%Y-%m-%d %H:%M:%S"`": 运行用户检查通过，当前用户为root"
  else
    echo `date "+%Y-%m-%d %H:%M:%S"`": 错误: 当前导入主机脚本需要以root用户运行，请切换到root用户下再执行!"
    exit 1
  fi
}
validateRunAsRoot

logFilePath="/root/surge-install-agent.log"
import_url=${master_url}/api/hosts/create
download_url=${master_url}/static/repo/sesame-1.1-1.noarch.rpm

function validateToolInstalled
{
  toolName=$1
  output=`$toolName --help 2>&1 | grep "command not found" | wc -l`
  if [ "$output" == "1" ]; then
    return 1
  else
    return 0
  fi
}

function installTools
{
  toolName=$@
  echo `date "+%Y-%m-%d %H:%M:%S"`": 安装依赖的工具包: $@"
  yum install -y $toolName 2>&1 >> $logFilePath
  echo `date "+%Y-%m-%d %H:%M:%S"`": 安装依赖的工具包结束!"
}

function InstallRequiredRuntimes
{
  #Require Python2.6 or last
  pythonVersion=`python -V 2>&1 | awk '{print $2}' | awk -F. '{print $1"."$2}'`
  pythonMajorVersion=`python -V 2>&1 | awk '{print $2}' | awk -F. '{print $1}'`
  pythonMinorVersion=`python -V 2>&1 | awk '{print $2}' | awk -F. '{print $2}'`
  if [ $pythonMajorVersion -eq 2 ] && [ $pythonMinorVersion -lt 6 ] ; then
    Tools='curl wget python python-devel python-setuptools python-pip tar jq unzip'
  else
    Tools='curl wget python-devel python-setuptools python-pip tar jq unzip'
  fi
  installTools $Tools
  if [ $pythonMinorVersion -eq 4 ];then
      wget ${master_url}/static/repo/jq -P /usr/bin/
      chmod +x /usr/bin/jq
  fi
  for tool in $Tools;do
    if [[ $tool == "python-devel" || $tool == "python-setuptools" || $tool == "python-pip" ]];then
       continue
    fi
    validateToolInstalled $tool
    if [ $? != 0 ];then
      echo `date "+%Y-%m-%d %H:%M:%S"`: "ERROR: $tool install failed, please check yum repo, repo configuration, network to make sure can install them."
      exit 101
    fi
  done
  pip install pika
}

export LC_ALL=C

function NetworkInfo
{
  #1) Get localhost's IP
  #Get localIP and remoteIP
  if [ -f /etc/redhat-release ];then
     #CentOS VMs
     majorVersion=`cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | awk -F. '{print $1}'`
     if [ "x$majorVersion" == "x7" ];then
         remoteIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $2}' | grep -v '^192' | grep -v '^10\.' | grep -v '^172'`
         if [ "x$remoteIP" == "x" ];then
             remoteIP=`curl ip.cn | awk -F'[： ]+' '{print $3}'`
             if [ "x$remoteIP" == "x" ];then
                 remoteIP=`curl api.ipify.org`
             fi
             localIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1'  | cut -d: -f2 | awk '{ print $2}'`
         else 
             localIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1'  | cut -d: -f2 | awk '{ print $2}' | grep -v "$remoteIP"`
         fi
     else
         remoteIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}' | grep -v '^192' | grep -v '^10\.' | grep -v '^172'`
         if [ "x$remoteIP" == "x" ];then
             remoteIP=`curl ip.cn | awk -F'[： ]+' '{print $3}'`
             if [ "x$remoteIP" == "x" ];then
                 remoteIP=`curl api.ipify.org`
             fi
             localIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1'  | cut -d: -f2 | awk '{ print $1}'`
         else 
             localIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1'  | cut -d: -f2 | awk '{ print $1}' | grep -v "$remoteIP"`
         fi
     fi
  else
       #Ubuntu or SUSE VMs
         remoteIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}' | grep -v '^192' | grep -v '^10\.' | grep -v '^172'`
         if [ "x$remoteIP" == "x" ];then
             remoteIP=`curl ip.cn | awk -F'[： ]+' '{print $3}'`
             if [ "x$remoteIP" == "x" ];then
                 remoteIP=`curl api.ipify.org`
             fi
             localIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1'  | cut -d: -f2 | awk '{ print $1}'`
         else 
             localIP=`LC_ALL=C ifconfig | grep 'inet '| grep -v '127.0.0.1'  | cut -d: -f2 | awk '{ print $1}' | grep -v "$remoteIP"`
         fi
  fi
  remoteIP=`echo $remoteIP | tr ' ' ','`
  localIP=`echo $localIP | tr ' ' ','`
}

function BlockInfo
{
  disk_number=`lsblk -dn | awk 'BEGIN{nu=0}{if($4~/G$/ && $6=="disk")nu+=1}END{print nu}'`
  disk_capacity=`lsblk -dn | awk 'BEGIN{sum=0}{if($4~/G$/ && $6=="disk")sum+=substr($4,0,length-1)}END{print sum}' | awk -F'.' '{if($2)$1+=1;print $1}'`
}

function MemoryInfo
{
  memory_capacity=`grep MemTotal /proc/meminfo | awk '{printf "%.1f", $2/1024/1024}' | awk -F '.' '{$1+=1;print $1}'`
}

function CpuInfo
{
  cpu_core=`grep 'model name' /proc/cpuinfo | wc -l`
}

function ImportServer
{
  NetworkInfo
  BlockInfo
  MemoryInfo
  CpuInfo
  echo `date "+%Y-%m-%d %H:%M:%S"`": 尝试向${import_url}导入服务器..."
  echo "curl $import_url -d disk_number=$disk_number -d disk_capacity=$disk_capacity -d memory_capacity=$memory_capacity -d cpu_core=$cpu_core -d public_ip=$remoteIP -d private_ip=$localIP -d idc_location_id=$idc_uuid"
  serverdata=`curl -s -H "apikey:$key" $import_url -d disk_number=$disk_number -d disk_capacity=$disk_capacity -d memory_capacity=$memory_capacity -d cpu_core=$cpu_core -d public_ip=$remoteIP -d private_ip=$localIP -d idc_location_id=$idc_uuid`
  echo `date "+%Y-%m-%d %H:%M:%S"`": 导入服务器结束"
  success=`echo $serverdata|jq '.success'`
  msg=`echo $serverdata|jq '.msg'`
  if [ "x$success" == "xtrue" ];then
      uuid=`echo $serverdata|jq '.msg.uuid'`
      if [ "$uuid" == "null" ];then
          echo `date "+%Y-%m-%d %H:%M:%S"`": 获取服务器UUID失败"
          exit 102
      else
          echo `date "+%Y-%m-%d %H:%M:%S"`": 获取服务器UUID=$uuid"
      fi
  else
      echo 服务器录入失败:$serverdata >> $logFilePath
      echo `date "+%Y-%m-%d %H:%M:%S"`": 服务器录入失败:$msg"
      exit 103
  fi
}

function InjectAgentData
{
  #Get AgentData
  injectAgentDataSuccess=False
  inject_url=${master_url}/cmdb/hosts/$uuid/agentdata
  echo `date "+%Y-%m-%d %H:%M:%S"`": 尝试从${inject_url}获取AgentData..."
  echo curl -L --insecure --silent --retry 3 --retry-delay 5 -m 60 $inject_url  >> $logFilePath
  agentdata=`curl -H "apikey:$key" -L --insecure --silent --retry 3 --retry-delay 3 -m 60 "${inject_url}"`
  echo `date "+%Y-%m-%d %H:%M:%S"`": 获取AgentData结束"
  echo agentdata=$agentdata  >> $logFilePath
  if [ "x$agentdata"  == "x" ];then
       injectAgentDataSuccess=False
  else
       injectAgentDataSuccess=True
  fi

  if [ "$injectAgentDataSuccess" == "False" ];then
     echo `date "+%Y-%m-%d %H:%M:%S"`": ERROR: 注入AgentData失败"
     exit 103
  fi 
}

function InstallAgent
{
  scriptDownloadedPath=/tmp/sesame-1.1-1.noarch.rpm
  echo `date "+%Y-%m-%d %H:%M:%S"`": 安装agent sesame..."
  echo `date "+%Y-%m-%d %H:%M:%S"`: "下载安装包..."
  curl -L -o $scriptDownloadedPath --retry 3 --retry-delay 5 --connect-timeout 10 -m 180 $download_url 2>&1 >> $logFilePath
  if [ $? -eq 0 ];then
      echo `date "+%Y-%m-%d %H:%M:%S"`": 下载命令为curl -L -o $scriptDownloadedPath --retry 3 --retry-delay 5 --connect-timeout 10 -m 180 $download_url 2>&1 >> $logFilePath"
      echo `date "+%Y-%m-%d %H:%M:%S"`": 下载成功, 开始安装"
      rpm -Uvh $scriptDownloadedPath
      if [ $? -eq 0 ];then
          if [ "$injectAgentDataSuccess" == "True" ];then
              echo `date "+%Y-%m-%d %H:%M:%S"`": 开始生成配置文件!"
              mkdir -p /etc/sesame
              echo $agentdata | base64 -d > /etc/sesame/sesame.json
              echo `date "+%Y-%m-%d %H:%M:%S"`": 配置文件生成成功!"
              /etc/init.d/sesame start
          else
              echo "AgentData获取失败,无法生成配置文件." >> $logFilePath
          fi
      fi
  else
      echo `date "+%Y-%m-%d %H:%M:%S"`": 下载命令为curl -L -o $scriptDownloadedPath --retry 3 --retry-delay 5 --connect-timeout 10 -m 180 $download_url 2>&1 >> $logFilePath"
      echo `date "+%Y-%m-%d %H:%M:%S"`": 下载失败..."
      exit 105
  fi
  rm -rf /tmp/sesame-agent*
}

#1. installRequiredRuntimes
InstallRequiredRuntimes
#2. importServer
ImportServer
#3. injectAgentData
InjectAgentData
#4. installAgent
InstallAgent
