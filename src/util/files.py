import os


class Files:
    @classmethod
    def ensure_dir_exists(cls, d):
        if not os.path.exists(d):
            os.makedirs(d)
        return d

    @classmethod
    def dir(cls, sub_dir=""):
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), "../..", sub_dir)
        )

    @classmethod
    def data_dir(cls, sub_dir=""):
        return os.path.join(cls.ensure_dir_exists(cls.dir("data")), sub_dir)

    @classmethod
    def rfc_dir(cls, sub_dir=""):
        return os.path.join(cls.ensure_dir_exists(cls.data_dir("rfc")), sub_dir)

    @classmethod
    def metadata_dir(cls, sub_dir=""):
        return os.path.join(cls.ensure_dir_exists(cls.data_dir("meta")), sub_dir)

    @classmethod
    def iesgs_file(cls):
        return cls.metadata_dir("IESGs.json")

    @classmethod
    def ad_term_starts_file(cls):
        return cls.metadata_dir("AD_term_starts.json")

    @classmethod
    def ad_term_ends_file(cls):
        return cls.metadata_dir("AD_term_ends.json")

    @classmethod
    def discusses_file(cls):
        return cls.data_dir("discusses.json")
