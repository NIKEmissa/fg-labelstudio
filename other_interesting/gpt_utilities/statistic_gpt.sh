while true; do
    # 每次循环等待 1 秒
    sleep 1
    
    # 统计 output/batch_label/ 目录下的文件数量
    cur=$(ls output/batch_label/ | wc -l)
    
    # 计算与上次统计相比，新增加的文件数
    diff=$((cur - prev))
    
    # 秒计数器增加 1
    sec=$((sec + 1))
    
    # 构建输出字符串，显示当前文件数和每秒新增文件数
    output="当前文件数: $cur, 每秒新增: $diff 个文件"
    
    # 每经过 60 秒（即一分钟）
    if [ $sec -ge 60 ]; then
        # 计算这一分钟内新增的文件数
        minute_diff=$((cur - minute_prev))
        # 在输出字符串中附加每分钟新增文件数的信息
        output="$output, 每分钟新增: $minute_diff 个文件"
        # 更新一分钟前的文件计数
        minute_prev=$cur
        # 重置秒计数器
        sec=0
    fi
    
    # 输出当前统计结果
    echo "$output"
    
    # 更新上次统计的文件数量
    prev=$cur
done
