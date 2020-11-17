import os
import shutil
import time

class Caller:
    def __init__(self, *fs, binpath="bin\\OpenPoseDemo.exe"):
        self.fs = fs
        self.binpath = binpath
        self.p = None
        self.output_dir = ".\\output"
        self.tmp_path = None

    def create_temp_fn(self):
        path = "./{}".format(time.time())
        os.makedirs(path)
        for fn,jfn in zip(self.fs,self.json_fs):
            if os.path.exists(jfn):
                continue
            tmp = os.path.join(path, os.path.basename(fn))
            shutil.copy(fn, tmp)
        self.tmp_path = os.path.normcase(path)
        return self.tmp_path

    @property
    def json_dir(self):
        path = os.path.join(self.output_dir,"json")
        os.makedirs(path,exist_ok=True)
        return path

    @property
    def render_dir(self):
        path = os.path.join(self.output_dir,'render')
        os.makedirs(path,exist_ok=True)
        return path

    def start(self,wait=True):
        path = self.create_temp_fn()

        cmd = "{self.binpath} " \
              "--image_dir {path}  " \
              "--write_json {self.json_dir} " \
              "--display 0 " \
              "--write_images {self.render_dir}".format(path=path,
                                                   self=self)
        print(cmd)
        from subprocess import Popen, PIPE, STDOUT
        self.p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE,  # 创建进程执行代码，并获取其输出流返回
                       stderr=STDOUT, close_fds=True)

        if wait:
            return self.wait()
        else:
            return None

    def wait(self):
        if self.p is None:
            return None

        while self.p.poll() is None:
            time.sleep(0.5)

        return self.p.poll()

    @property
    def json_fs(self):
        prefix = [os.path.basename(os.path.splitext(f)[0]) for f in self.fs]
        return [os.path.join(self.json_dir,"{}_keypoints.json").format(f) for f in prefix]

    @property
    def render_fs(self):
        prefix = [os.path.basename(os.path.splitext(f)[0]) for f in self.fs]
        return [os.path.join(self.render_dir, "{}_rendered.png").format(f) for f in prefix]


if __name__ == '__main__':

    pass