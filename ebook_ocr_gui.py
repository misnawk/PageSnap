import pyautogui
import pytesseract
from PIL import Image, ImageChops, ImageTk
import keyboard
import time
import os
from datetime import datetime
import threading
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import json
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import glob

# Tesseract 경로 설정 (Windows의 경우 필요)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class EbookOCRGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("📚 E-book 자동 텍스트 추출기")
        self.root.geometry("1100x850")
        self.root.resizable(True, True)

        # 폴더 구조 설정
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_dir = os.path.join(self.base_dir, "config")
        self.output_dir = os.path.join(self.base_dir, "output")
        self.screenshot_dir = os.path.join(self.output_dir, "screenshots")
        self.text_dir = os.path.join(self.output_dir, "text")
        self.pdf_dir = os.path.join(self.output_dir, "pdf")

        # 필요한 폴더 생성
        for directory in [self.config_dir, self.screenshot_dir, self.text_dir, self.pdf_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        # 변수 초기화
        self.output_file = os.path.join(self.text_dir, "extracted_ebook.txt")
        self.lang = 'kor+eng'
        self.is_running = False
        self.last_screenshot = None
        self.capture_region = None
        self.page_count = 0
        self.config_file = os.path.join(self.config_dir, "capture_config.json")
        self.capture_thread = None
        self.preview_photo = None  # 미리보기 이미지 참조 유지


        # 저장된 설정 불러오기
        self.load_config()

        # GUI 구성
        self.create_widgets()

    def create_widgets(self):
        """GUI 위젯 생성"""
        # 타이틀
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)

        title_label = tk.Label(
            title_frame,
            text="📚 E-book 자동 텍스트 추출기",
            font=("맑은 고딕", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)

        # 메인 컨텐츠 - 좌우 분할
        content_frame = tk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 왼쪽 패널 (설정 및 컨트롤)
        left_frame = tk.Frame(content_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 오른쪽 패널 (미리보기)
        right_frame = tk.Frame(content_frame, width=400)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

        # 메인 컨텐츠
        main_frame = tk.Frame(left_frame, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 캡처 영역 설정 섹션
        region_frame = tk.LabelFrame(
            main_frame,
            text="🖱️ 캡처 영역 설정",
            font=("맑은 고딕", 12, "bold"),
            padx=15,
            pady=15
        )
        region_frame.pack(fill=tk.X, pady=(0, 15))

        region_info_text = "전체 화면" if not self.capture_region else f"{self.capture_region[2]} x {self.capture_region[3]}"
        self.region_label = tk.Label(
            region_frame,
            text=f"현재 설정: {region_info_text}",
            font=("맑은 고딕", 10)
        )
        self.region_label.pack(pady=(0, 10))

        region_btn_frame = tk.Frame(region_frame)
        region_btn_frame.pack()

        tk.Button(
            region_btn_frame,
            text="마우스로 영역 선택",
            command=self.select_region_gui,
            bg="#3498db",
            fg="white",
            font=("맑은 고딕", 10, "bold"),
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            region_btn_frame,
            text="전체 화면",
            command=self.set_fullscreen,
            bg="#95a5a6",
            fg="white",
            font=("맑은 고딕", 10),
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        tk.Button(
            region_btn_frame,
            text="중앙 영역",
            command=self.set_center_region,
            bg="#95a5a6",
            fg="white",
            font=("맑은 고딕", 10),
            padx=15,
            pady=8,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)

        # 모드 선택 섹션
        mode_frame = tk.LabelFrame(
            main_frame,
            text="🎯 작동 모드 선택",
            font=("맑은 고딕", 12, "bold"),
            padx=15,
            pady=15
        )
        mode_frame.pack(fill=tk.X, pady=(0, 15))

        # 설정 값들
        settings_frame = tk.Frame(mode_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))

        # 확인 간격
        tk.Label(settings_frame, text="확인 간격(초):", font=("맑은 고딕", 9)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.interval_var = tk.StringVar(value="0.5")
        tk.Entry(settings_frame, textvariable=self.interval_var, width=10).grid(row=0, column=1, padx=10, pady=5)

        # 민감도
        tk.Label(settings_frame, text="민감도(%):", font=("맑은 고딕", 9)).grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20, 0))
        self.sensitivity_var = tk.StringVar(value="5")
        tk.Entry(settings_frame, textvariable=self.sensitivity_var, width=10).grid(row=0, column=3, padx=10, pady=5)

        # 민감도 설명
        sensitivity_info = tk.Label(
            settings_frame,
            text="💡 민감도: 낮을수록 작은 변화도 감지 (권장: 3-7)",
            font=("맑은 고딕", 8),
            fg="#7f8c8d"
        )
        sensitivity_info.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))

        # 모드 버튼들
        mode_btn_frame = tk.Frame(mode_frame)
        mode_btn_frame.pack()

        tk.Button(
            mode_btn_frame,
            text="🤖 자동 페이지 변화 감지 시작",
            command=self.start_auto_detect,
            bg="#27ae60",
            fg="white",
            font=("맑은 고딕", 12, "bold"),
            padx=20,
            pady=15,
            cursor="hand2"
        ).pack(pady=5, fill=tk.X)

        self.stop_btn = tk.Button(
            mode_btn_frame,
            text="⏹️ 중지",
            command=self.stop_capture,
            bg="#e74c3c",
            fg="white",
            font=("맑은 고딕", 11, "bold"),
            padx=20,
            pady=10,
            cursor="hand2",
            state=tk.DISABLED
        )
        self.stop_btn.pack(pady=5, fill=tk.X)

        # PDF 내보내기 버튼
        tk.Button(
            mode_btn_frame,
            text="📄 PDF로 내보내기",
            command=self.export_to_pdf,
            bg="#9b59b6",
            fg="white",
            font=("맑은 고딕", 11),
            padx=20,
            pady=10,
            cursor="hand2"
        ).pack(pady=5, fill=tk.X)

        # 상태 표시 섹션
        status_frame = tk.LabelFrame(
            main_frame,
            text="📊 상태",
            font=("맑은 고딕", 12, "bold"),
            padx=15,
            pady=15
        )
        status_frame.pack(fill=tk.BOTH, expand=True)

        self.status_text = scrolledtext.ScrolledText(
            status_frame,
            height=8,
            font=("맑은 고딕", 9),
            bg="#f8f9fa",
            wrap=tk.WORD
        )
        self.status_text.pack(fill=tk.BOTH, expand=True)

        self.log("프로그램이 준비되었습니다.")
        if self.capture_region:
            self.log(f"저장된 캡처 영역을 불러왔습니다: {self.capture_region[2]}x{self.capture_region[3]}")

        # 미리보기 패널 생성
        self.create_preview_panel(right_frame)

    def create_preview_panel(self, parent):
        """미리보기 패널 생성"""
        preview_frame = tk.LabelFrame(
            parent,
            text="📸 최근 캡처 미리보기",
            font=("맑은 고딕", 12, "bold"),
            padx=15,
            pady=15
        )
        preview_frame.pack(fill=tk.BOTH, expand=True)

        # 미리보기 라벨
        self.preview_label = tk.Label(
            preview_frame,
            text="캡처된 이미지가 여기에 표시됩니다",
            bg="#ecf0f1",
            relief=tk.SUNKEN,
            font=("맑은 고딕", 10),
            fg="#7f8c8d"
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # 페이지 정보 라벨
        self.page_info_label = tk.Label(
            preview_frame,
            text="대기 중...",
            font=("맑은 고딕", 9),
            fg="#34495e"
        )
        self.page_info_label.pack(pady=(10, 0))

    def log(self, message):
        """상태창에 로그 출력 (thread-safe)"""
        def _log_impl():
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.status_text.see(tk.END)
            except Exception:
                # GUI가 종료되었거나 사용 불가능한 경우 무시
                pass

        # 메인 스레드에서 실행되도록 스케줄링
        try:
            self.root.after(0, _log_impl)
        except Exception:
            # 메인 루프가 실행 중이 아닌 경우 콘솔에 출력
            print(f"[LOG] {message}")

    def update_preview(self, screenshot):
        """미리보기 이미지 업데이트 (thread-safe)"""
        def _update_impl():
            try:
                # 이미지 크기 조정 (최대 380x500)
                img = screenshot.copy()
                img.thumbnail((380, 500), Image.Resampling.LANCZOS)

                # PIL 이미지를 PhotoImage로 변환
                self.preview_photo = ImageTk.PhotoImage(img)

                # 라벨에 이미지 설정
                self.preview_label.config(image=self.preview_photo, text="")

                # 페이지 정보 업데이트
                self.page_info_label.config(
                    text=f"페이지 {self.page_count} | {img.size[0]} x {img.size[1]}"
                )
            except Exception as e:
                print(f"[미리보기 업데이트 실패] {e}")

        # 메인 스레드에서 실행되도록 스케줄링
        try:
            self.root.after(0, _update_impl)
        except Exception:
            # 메인 루프가 실행 중이 아닌 경우 무시
            pass

    def select_region_gui(self):
        """마우스로 영역 선택"""
        self.log("영역 선택 화면을 표시합니다...")
        self.root.update()

        region = self.select_region_with_mouse()
        if region:
            self.capture_region = region
            self.region_label.config(text=f"현재 설정: {region[2]} x {region[3]}")
            self.log(f"✓ 영역 선택 완료: {region[2]} x {region[3]}")
            self.save_config()
        else:
            self.log("영역 선택이 취소되었습니다.")

    def select_region_with_mouse(self):
        """마우스 드래그로 영역 선택"""
        select_window = tk.Toplevel()
        select_window.attributes('-alpha', 0.3)
        select_window.attributes('-fullscreen', True)
        select_window.attributes('-topmost', True)
        select_window.configure(bg='black')

        canvas = tk.Canvas(select_window, cursor="cross", bg='black', highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        info_text = canvas.create_text(
            select_window.winfo_screenwidth() // 2, 50,
            text="마우스를 드래그하여 캡처 영역을 선택하세요 (ESC: 취소)",
            font=("맑은 고딕", 20, "bold"),
            fill="yellow"
        )

        rect = None
        start_x = start_y = 0
        region = None

        def on_mouse_down(event):
            nonlocal start_x, start_y, rect
            start_x, start_y = event.x, event.y
            if rect:
                canvas.delete(rect)
            rect = canvas.create_rectangle(
                start_x, start_y, start_x, start_y,
                outline='red', width=3, fill='white', stipple='gray50'
            )

        def on_mouse_move(event):
            nonlocal rect
            if rect:
                canvas.coords(rect, start_x, start_y, event.x, event.y)
                width = abs(event.x - start_x)
                height = abs(event.y - start_y)
                canvas.itemconfig(info_text,
                    text=f"영역 크기: {width} x {height} (놓으면 확정)")

        def on_mouse_up(event):
            nonlocal region
            coords = canvas.coords(rect)
            if coords:
                x1, y1, x2, y2 = coords
                left = int(min(x1, x2))
                top = int(min(y1, y2))
                right = int(max(x1, x2))
                bottom = int(max(y1, y2))

                width = right - left
                height = bottom - top

                if width > 10 and height > 10:
                    region = (left, top, width, height)
                    select_window.quit()
                else:
                    messagebox.showwarning("경고", "영역이 너무 작습니다. 다시 선택해주세요.")

        def on_escape(event):
            select_window.quit()

        canvas.bind('<Button-1>', on_mouse_down)
        canvas.bind('<B1-Motion>', on_mouse_move)
        canvas.bind('<ButtonRelease-1>', on_mouse_up)
        select_window.bind('<Escape>', on_escape)

        select_window.mainloop()
        select_window.destroy()

        return region

    def set_fullscreen(self):
        """전체 화면으로 설정"""
        self.capture_region = None
        self.region_label.config(text="현재 설정: 전체 화면")
        self.log("✓ 전체 화면으로 설정되었습니다.")
        self.save_config()

    def set_center_region(self):
        """화면 중앙 영역으로 설정"""
        screen_width, screen_height = pyautogui.size()
        width = int(screen_width * 0.6)
        height = int(screen_height * 0.8)
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.capture_region = (x, y, width, height)
        self.region_label.config(text=f"현재 설정: {width} x {height} (중앙)")
        self.log(f"✓ 중앙 영역으로 설정되었습니다: {width} x {height}")
        self.save_config()


    def save_config(self):
        """설정 저장"""
        try:
            config = {
                'capture_region': self.capture_region,
                'interval': self.interval_var.get(),
                'sensitivity': self.sensitivity_var.get(),
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            self.log(f"설정 저장 실패: {e}")

    def load_config(self):
        """설정 불러오기"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.capture_region = config.get('capture_region')

                    # 매크로 설정이 있다면 GUI에도 반영

        except Exception as e:
            print(f"설정 불러오기 실패: {e}")

    def capture_screenshot(self):
        """스크린샷 캡처"""
        if self.capture_region:
            screenshot = pyautogui.screenshot(region=self.capture_region)
        else:
            screenshot = pyautogui.screenshot()
        return screenshot

    def extract_text_from_image(self, image):
        """이미지에서 텍스트 추출"""
        try:
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text
        except Exception as e:
            self.log(f"OCR 오류: {e}")
            return ""

    def save_capture(self, screenshot, text):
        """스크린샷과 텍스트 저장"""
        self.page_count += 1
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        screenshot_path = os.path.join(self.screenshot_dir, f"page_{self.page_count:03d}_{timestamp}.png")
        screenshot.save(screenshot_path)

        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*50}\n")
            f.write(f"페이지 {self.page_count} | {timestamp}\n")
            f.write(f"{'='*50}\n")
            f.write(text)
            f.write("\n")

        self.log(f"✓ 페이지 {self.page_count} 저장 완료")

        # 미리보기 업데이트
        self.update_preview(screenshot)

    def images_are_different(self, img1, img2, threshold=5):
        """두 이미지의 차이 비율 계산"""
        if img1.size != img2.size:
            self.log(f"🔍 이미지 크기 변화 감지 (다른 크기)")
            return True

        # 이미지를 RGB로 변환 (투명도 제거)
        if img1.mode != 'RGB':
            img1 = img1.convert('RGB')
        if img2.mode != 'RGB':
            img2 = img2.convert('RGB')

        diff = ImageChops.difference(img1, img2)
        diff_array = np.array(diff)

        # 각 채널별로 차이 계산
        total_pixels = diff_array.shape[0] * diff_array.shape[1]
        changed_pixels = np.count_nonzero(np.sum(diff_array, axis=2) > 30)
        change_ratio = (changed_pixels / total_pixels) * 100

        # 디버그 정보 출력
        self.log(f"🔍 변화율: {change_ratio:.2f}% (임계값: {threshold}%)")

        return change_ratio > threshold

    def start_auto_detect(self):
        """자동 페이지 변화 감지 시작"""
        if not self.capture_region:
            response = messagebox.askyesno(
                "캡처 영역 미설정",
                "캡처 영역이 설정되지 않았습니다.\n전체 화면으로 진행하시겠습니까?"
            )
            if not response:
                return

        try:
            interval = float(self.interval_var.get())
            sensitivity = float(self.sensitivity_var.get())
        except ValueError:
            messagebox.showerror("오류", "확인 간격과 민감도는 숫자여야 합니다.")
            return

        self.log("="*40)
        self.log("🤖 자동 페이지 변화 감지 모드 시작")
        self.log(f"확인 간격: {interval}초, 민감도: {sensitivity}%")
        self.log("="*40)

        messagebox.showinfo(
            "준비",
            "e-book을 열고 준비되면 확인을 누르세요.\n3초 후 자동 감지가 시작됩니다."
        )

        self.log("3초 후 시작...")
        self.root.update()
        time.sleep(3)

        # 첫 페이지 캡처
        self.last_screenshot = self.capture_screenshot()
        text = self.extract_text_from_image(self.last_screenshot)
        self.save_capture(self.last_screenshot, text)

        self.is_running = True
        self.stop_btn.config(state=tk.NORMAL)

        # 백그라운드 스레드에서 실행
        self.capture_thread = threading.Thread(
            target=self.auto_detect_loop,
            args=(interval, sensitivity),
            daemon=True
        )
        self.capture_thread.start()

    def auto_detect_loop(self, interval, sensitivity):
        """자동 감지 루프"""
        while self.is_running:
            time.sleep(interval)

            if not self.is_running:
                break

            current_screenshot = self.capture_screenshot()

            if self.images_are_different(self.last_screenshot, current_screenshot, sensitivity):
                self.log("📄 페이지 변화 감지! 캡처 중...")

                text = self.extract_text_from_image(current_screenshot)
                self.save_capture(current_screenshot, text)

                self.last_screenshot = current_screenshot

        self.log("자동 감지가 중지되었습니다.")

    def stop_capture(self):
        """캡처 중지"""
        self.is_running = False
        self.stop_btn.config(state=tk.DISABLED)
        self.log(f"⏹️ 중지됨 (총 {self.page_count}페이지 캡처)")

    def export_to_pdf(self):
        """스크린샷들을 PDF로 내보내기"""
        # 스크린샷 파일 찾기
        screenshot_files = sorted(glob.glob(os.path.join(self.screenshot_dir, "*.png")))

        if not screenshot_files:
            messagebox.showwarning("경고", "내보낼 스크린샷이 없습니다.\n먼저 페이지를 캡처해주세요.")
            return

        # PDF 저장 위치 선택 (기본 경로를 pdf 폴더로)
        pdf_filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialdir=self.pdf_dir,
            initialfile=f"ebook_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        if not pdf_filename:
            return  # 사용자가 취소함

        try:
            self.log(f"PDF 생성 중... ({len(screenshot_files)}개 페이지)")
            self.root.update()

            # PDF 생성
            c = canvas.Canvas(pdf_filename, pagesize=A4)
            page_width, page_height = A4

            for idx, img_path in enumerate(screenshot_files):
                self.log(f"처리 중: {idx+1}/{len(screenshot_files)}")
                self.root.update()

                # 이미지 열기
                img = Image.open(img_path)
                img_width, img_height = img.size

                # A4 페이지에 맞게 이미지 크기 조정 (여백 20 포인트)
                margin = 40
                available_width = page_width - 2 * margin
                available_height = page_height - 2 * margin

                # 비율 유지하며 크기 조정
                ratio = min(available_width / img_width, available_height / img_height)
                new_width = img_width * ratio
                new_height = img_height * ratio

                # 이미지를 페이지 중앙에 배치
                x = (page_width - new_width) / 2
                y = (page_height - new_height) / 2

                # 이미지 추가
                c.drawImage(img_path, x, y, width=new_width, height=new_height)

                # 페이지 번호 추가
                c.setFont("Helvetica", 10)
                c.drawString(page_width / 2 - 20, 20, f"Page {idx + 1}")

                # 다음 페이지로 (마지막 페이지가 아니면)
                if idx < len(screenshot_files) - 1:
                    c.showPage()

            # PDF 저장
            c.save()

            self.log(f"✓ PDF 생성 완료! 저장됨: {pdf_filename}")
            messagebox.showinfo("완료", f"PDF가 성공적으로 생성되었습니다!\n\n파일: {os.path.basename(pdf_filename)}\n페이지 수: {len(screenshot_files)}")

        except Exception as e:
            self.log(f"❌ PDF 생성 실패: {e}")
            messagebox.showerror("오류", f"PDF 생성 중 오류가 발생했습니다:\n{e}")

    def run(self):
        """GUI 실행"""
        self.root.mainloop()


if __name__ == "__main__":
    app = EbookOCRGUI()
    app.run()
