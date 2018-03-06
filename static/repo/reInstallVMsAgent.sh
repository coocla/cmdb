#!/bin/bash
#author: coocla
#description: Install surge agent. just so~ 

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
download_url=${master_url}/static/repo/sesame-1.0-1.noarch.rpm

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
  output=`yum install -y $toolName 2>&1 >> $logFilePath`
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
  installTools $Tool
  for tool in $Tool;do
    validateToolInstalled $tool
    if [ $? != 0 ];then
      echo `date "+%Y-%m-%d %H:%M:%S"`: "ERROR: $tool install failed, please check yum repo, repo configuration, network to make sure can install them."
      exit 101
    fi
  done
}

export LC_ALL=C
function InjectAgentData
{
  #Get AgentData
  injectAgentDataSuccess=False
  inject_url=${master_url}/cmdb/host/$uuid/agentdata
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
  pip install pika
}

function InstallAgent
{
  scriptDownloadedPath=/tmp/sesame-1.0-1.noarch.rpm
  echo `date "+%Y-%m-%d %H:%M:%S"`": 安装agent sesame..."
  echo `date "+%Y-%m-%d %H:%M:%S"`: "下载安装包..."
  curlOutput=`curl -L -o $scriptDownloadedPath --retry 3 --retry-delay 5 --connect-timeout 10 -m 180 $download_url 2>&1 >> $logFilePath`
  if [ $? eq 0 ];then
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
    
}

#1. installRequiredRuntimes
InstallRequiredRuntimes
#2. injectAgentData
InjectAgentData
#3. installAgent
InstallAgent
