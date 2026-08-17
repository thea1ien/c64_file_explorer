C64_File_Explorer - A Python program to perform various functions on C64 disk images and files!


NOTE: This program is still in BETA. While some features do work, others do not work at all or may work incorrectly. Before testing this on any image files, please make sure you have a backup just in case!!

Currently the program has a dual-pane explorer setup (similar to Norton Commander/Midnight Commander) It currently supports mounting the following C64 disk image formats:
 
	D64 - Standard 1541 disk image storing data at the sector level
 
	G64 - An enhanced 1541 disk image with data stored as GCR encoded data, just like a real 1541 stores its 
			data D71 - Similar to the D64, except storage for a 1571 disk image at the sector level
 
	D81 - A disk image of a 1581 disk 

	DNP - CMD (Creative Micro Designs) Native Partition image. Used on various CMD devices, a flexible 
			partition that can be as large as 16mb

	DHD - CMD Hard Drive disk image


(Currently in progress is D2M and D4M disk images, for CMD's FD floppy drive devices) 
Please note that currently most functions are read-only still. 
The sector/editor and BAM however are able to make changes

Currently working functions:

	Able to browse nested files. So you can open a DHD hard drive image, go into a DNP partition in the DHD, 
	open a G64 image, and open files there!
	
	A track/sector editor for all disk images (minus DHD itself). Supports following sector links by the cursor 
	location. You can enter text or change bytes as a hex value.
	
	Support on DNP's include being able to go into DNP subdirectories
	
	Able to make 1581 subdirectory/partitions on 1581 disk images. This is a visual wizard that lets you see 
	where you can start a partition, then choose the ending. You can then go inside that partition and make 
	one or more partitions the are nested inside.
	
	And the BAM editor below will show you the BAM for the partition you are currently in. A BAM (Block 
	Allocation Map editor) - Allows you to examine the BAM on any of the disk image formats (except for DHD 
	which does not have a BAM). You can navigate the BAM, to see sectors that are allocated or not and change 
	them if you wish. The BAM display even supports DNP images. I'm not aware of another utility that does this)
	
	File viewers: 
	ASCII viewer 
	A PETSCII to ANSI viewer (lets you view PETSCII text files including those with 
	PETSCII color grx such as BBS's commonly. It uses ANSI to display so it's not perfect but it does a decent 
	job.) 
	True PETSCII viewer (this requires that you have the C64 Mono Pro.ttf font that was released by Style.
	It must be installed and set as the active font for your terminal) 
	https://style64.org/release/c64-truetype-v1.2.1-style 
	A HEX display viewer - Allows you to examine a file at the binary level as both hex and text display. 
	
	Currently it also supports .LNX (lynx) archive files. 
	There also is a graphical (pygame) visual mode, which is intended to have all of the same features as the 
	text/curses standard display. It's planned to have this be able to handle displaying PETSCII text files 
	without needing to install the C64 Mono Pro.ttf font

This is still a work in progress. I still need to finish getting d2m and d4m installed, verify that basic read
 and write (sector level) access is working. Then I can move onto getting file copying (copy files from an 
 image) and writing (able to save files to an image), which includes being able to save to a file that is 
 nested inside several images. A BASIC program display option An ML disassembler viewer Mouse clickable support
 as well as Home and End keys to quickly move to the top or bottom of lists Change file types Support for other
 archive formats including 4-pack zip-code, 6-pack zip-code, ARC, LBR, WRA, SDA and SFX There might be more to 
 come as I progress further along!

 Screenshots:
 <img width="938" height="472" alt="image" src="https://github.com/user-attachments/assets/d0539a3c-5edd-4150-98e6-6ff5fef29314" />
