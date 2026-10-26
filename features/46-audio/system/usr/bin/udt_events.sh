#!/bin/bash

. /etc/profile

#KEY_VOLUMEUP=115
#KEY_VOLUMEDOWN=114

volume_ctrl()
{
        VOLSTEP=3
        CURRENTVOL=$(get_ee_setting "audio.volume")
        echo $CURRENTVOL
        MAXVOL=100
        MINVOL=0
        if [ "${1}" == "+" ]; then
                STEPVOL=$(($CURRENTVOL+$VOLSTEP))
        elif [ "${1}" == "-" ]; then
                STEPVOL=$(($CURRENTVOL-$VOLSTEP))
        else
                STEPVOL=${1}
        fi
        if [[ $STEPVOL -ge $MAXVOL ]];then
                STEPVOL=$MAXVOL
        fi
        if [[ $STEPVOL -le $MINVOL ]];then
                STEPVOL=$MINVOL
        fi
        echo $STEPVOL

        # R36: a escala e o mudo ficam no audio-ganho; sem ele vale a escala de fábrica abaixo
        if [ -x /usr/lib/r36/audio-ganho ]; then
                /usr/lib/r36/audio-ganho volume ${STEPVOL}
                return
        fi
		scaled=$(( (STEPVOL * 43 + 50) / 100 + 20 ))
        amixer cset name='speaker volume control'  ${scaled}
        set_ee_setting "audio.volume" ${STEPVOL}

}


volume_up_active=0
volume_down_active=0


repeat_volume_ctrl() {
    local op=$1
    while true; do
        volume_ctrl "$op"
        sleep 0.2
        if [[ "$op" == "+" && $volume_up_active -eq 0 ]]; then
            break
        elif [[ "$op" == "-" && $volume_down_active -eq 0 ]]; then
            break
        fi
    done
}



evtest "/dev/input/event1" | while read line; do
    if echo "$line" | grep "KEY_VOLUMEUP" | grep  "value 1"; then
        if [[ $volume_up_active -eq 0 ]]; then
            volume_up_active=1
            repeat_volume_ctrl "+" &
            repeat_up_pid=$!
        fi
    elif echo "$line" | grep "KEY_VOLUMEUP" | grep "value 0"; then
        volume_up_active=0
        kill $repeat_up_pid 2>/dev/null
    fi

    if echo "$line" | grep "KEY_VOLUMEDOWN" | grep "value 1"; then
        if [[ $volume_down_active -eq 0 ]]; then
            volume_down_active=1
            repeat_volume_ctrl "-" &
            repeat_down_pid=$!
        fi
    elif echo "$line" | grep "KEY_VOLUMEDOWN" | grep "value 0"; then
        volume_down_active=0
        kill $repeat_down_pid 2>/dev/null
    fi
done

#evtest "/dev/input/event1" | while read line; do
#        if echo "$line" | grep "KEY_VOLUMEUP"| grep "value 1";then
#                volume_ctrl +
#        fi
#
#        if echo "$line" | grep "KEY_VOLUMEDOWN"| grep "value 1";then
#                volume_ctrl -
#        fi
#done
