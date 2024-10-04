#!/bin/bash

# 获取所有监听中的端口信息
netstat -tuln | grep LISTEN | awk '{print $4}' | sed 's/.*://g' | sort -u | while read port; do
    # 输出端口信息
    echo "端口: $port"
    
    # 使用 fuser 查看占用该端口的进程ID
    pid=$(sudo fuser $port/tcp 2>/dev/null)

    if [ -z "$pid" ]; then
        echo "无进程占用该端口"
    else
        # 使用 ps 查看该进程的详细信息
        ps -p $pid -o pid,cmd --no-headers
    fi
    echo "---------------------------"
done

