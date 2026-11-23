verify_and_bootstrap_dependencies()


VFSDriverRegistry.register_format(".d64", D64FileSystemPlugin)


VFSDriverRegistry.register_format(".d71", D71FileSystemPlugin)


VFSDriverRegistry.register_format(".dnp", DNPFileSystemPlugin)


VFSDriverRegistry.register_format(".dhd", DHDFileSystemPlugin)


VFSDriverRegistry.register_format(".d2m", D2MFileSystemPlugin)


VFSDriverRegistry.register_format(".d4m", D4MFileSystemPlugin)


VFSDriverRegistry.register_format(".lnx", LNXFileSystemPlugin)


VFSDriverRegistry.register_format(".d81", D81FileSystemPlugin)


VFSDriverRegistry.register_format(".g64", G64FileSystemPlugin)


if __name__ == "__main__":
	curses.wrapper(main_orchestration_loop)


