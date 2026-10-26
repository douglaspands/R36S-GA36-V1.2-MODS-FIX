#!/bin/bash

. /etc/profile
POWER_KEY_FILE="/sys/devices/platform/micro_gamepad/power_key"
ACTION_SUSPEND="systemctl suspend"
system_sleeping=0
echo "1" > /sys/devices/platform/micro_gamepad/wake_lock #lock

while true; do
    key_value=$(cat "$POWER_KEY_FILE")
    if [ "$key_value" == "1" ]; then
        echo "0" > "$POWER_KEY_FILE"
		if [ "$system_sleeping" -eq 0 ]; then
			echo "0" > /sys/devices/platform/micro_gamepad/wake_lock #unlock
			#echo powersave   > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
			#echo 2 > /sys/devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene
			#echo 0  > /sys/class/gpio_sw/PX1/data
			touch /tmp/.system_suspending
			echo "0" > /sys/devices/virtual/disp/disp/attr/lcdbl
			amixer cset name='Audio speaker out' 0
			amixer cset name='Audio headphone out' 0

			sync
			system_sleeping=1
			
			#echo powersave   > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
			$ACTION_SUSPEND
		else
			echo "1" > /sys/devices/platform/micro_gamepad/wake_lock #lock
			system_sleeping=0
			echo  on  > /sys/power/state

			maxperf
			rm -f /tmp/.system_suspending
			brightness=$(get_ee_setting brightness.level)
			scaled_value=$(( (brightness * 255 + 50) / 100 ))
			echo $scaled_value  > /sys/devices/virtual/disp/disp/attr/lcdbl
			amixer cset name='Audio speaker out' 1
			amixer cset name='Audio headphone out' 1

			#echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
			#echo 1  > /sys/class/gpio_sw/PX1/data
			#echo 0 > /sys/devices/platform/sunxi-ddrfreq/devfreq/sunxi-ddrfreq/dsm/scene

			current_state=$(cat /sys/class/switch/h2w/state)
			case "$current_state" in
				"1"|"2")
					amixer cset name='Speaker Function' headset
					amixer cset name='Speaker Function' spk
					;;
				*)
					amixer cset name='Speaker Function' headset
					amixer cset name='Speaker Function' spk
					;;
			esac
			# R36: reaplica o ganho de áudio depois da troca do Speaker Function
			if [ -x /usr/lib/r36/audio-ganho ]; then /usr/lib/r36/audio-ganho aplica; fi

		fi
    fi
    sleep 0.2
done

#evtest "/dev/input/event0" | while read line; do
#        if echo "$line" | grep "KEY_POWER"| grep "value 1";then
#			if [ "$system_sleeping" -eq 0 ]; then #suspend
#				echo "0" > /sys/devices/platform/micro_gamepad/wake_lock #unlock
#				system_sleeping=1
#				$ACTION_SUSPEND
#			else #resume
#				echo "1" > /sys/devices/platform/micro_gamepad/wake_lock #lock
#				system_sleeping=0
#				echo  on  > /sys/power/state
#			fi
#        fi
#		sleep 0.2
#done
