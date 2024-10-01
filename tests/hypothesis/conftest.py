from hypothesis import Phase, Verbosity, settings

settings.register_profile("debug", settings(verbosity=Verbosity.verbose, phases=list(Phase)[:4]))
settings.load_profile("debug")
