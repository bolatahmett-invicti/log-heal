"""
LogHeal - Multi-Agent ELK Log Analyzer and Auto-Fix System
Each agent performs its task and passes information to the next agent
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class LogAnalysis:
    """Log analysis results"""
    error_type: str
    error_message: str
    stack_trace: str
    affected_files: List[str]
    severity: str
    timestamp: str


@dataclass
class Solution:
    """Proposed solution"""
    description: str
    affected_files: List[str]
    code_changes: Dict[str, str]
    tests_needed: List[str]


@dataclass
class GitOperation:
    """Git operation results"""
    branch_name: str
    commit_message: str
    files_changed: List[str]
    success: bool


@dataclass
class ErrorContext:
    """Error location and root cause analysis"""
    error_location: str
    root_cause: str
    relevant_code: str
    summary: str
    relevant_files: List[str]  # Relevant files found via RAG


class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, name: str):
        self.name = name
        self.api_endpoint = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4o"  # or "gpt-4-turbo", "gpt-3.5-turbo"
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not found. "
                "Please set your API key: $env:OPENAI_API_KEY='your-key-here'"
            )
    
    async def call_claude(self, prompt: str, max_tokens: int = 4000) -> str:
        """Calls the OpenAI API"""
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_endpoint, json=payload, headers=headers) as response:
                data = await response.json()
                
                # Error handling
                if response.status != 200:
                    error_msg = data.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"OpenAI API error ({response.status}): {error_msg}")
                
                if 'choices' not in data or len(data['choices']) == 0:
                    raise Exception(f"API response not in expected format: {data}")
                
                return data['choices'][0]['message']['content']
    
    def log(self, message: str):
        """Agent logging"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{self.name}] {message}")


class CodebaseProvider:
    """Indexes codebase and retrieves relevant code snippets via RAG"""
    
    def __init__(self, repo_path: str = "C:\\Users\\AhmetBolat\\Projects\\Claude\\TestSystem", file_extensions: List[str] = None):
        self.repo_path = Path(repo_path)
        self.file_extensions = file_extensions or ['.py', '.java', '.cs', '.js', '.ts', '.go', '.rb']
        self.file_index: Dict[str, str] = {}  # filename -> full_path
        self.class_index: Dict[str, List[str]] = {}  # classname -> [file_paths]
        self._build_index()
    
    def _build_index(self):
        """Index codebase - scan file and class names"""
        import re
        
        # Excluded directories
        excluded_dirs = {'.venv', 'venv', 'env', 'node_modules', '.git', '__pycache__', 
                        'bin', 'obj', 'build', 'dist', '.pytest_cache', '.mypy_cache',
                        'site-packages', 'Lib', 'lib', 'packages'}
        
        for file_path in self.repo_path.rglob('*'):
            # Check excluded directories
            if any(excluded in file_path.parts for excluded in excluded_dirs):
                continue
                
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                # Index filename
                self.file_index[file_path.name] = str(file_path)
                
                # Extract class names (simple regex)
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    
                    # Java/C#/TypeScript class pattern
                    class_patterns = [
                        r'class\s+(\w+)',  # class ClassName
                        r'interface\s+(\w+)',  # interface InterfaceName
                        r'public\s+class\s+(\w+)',  # public class ClassName
                    ]
                    
                    for pattern in class_patterns:
                        matches = re.findall(pattern, content)
                        for class_name in matches:
                            if class_name not in self.class_index:
                                self.class_index[class_name] = []
                            self.class_index[class_name].append(str(file_path))
                except Exception:
                    continue
    
    def find_relevant_files(self, stack_trace: str, error_message: str, max_files: int = 10) -> List[Dict[str, str]]:
        """Find relevant files from stack trace and error message"""
        import re
        
        relevant_files = []
        seen_paths = set()
        
        # 1. Extract filenames from stack trace
        file_patterns = [
            r'at\s+[\w.]+\(([\w.]+):(\d+)\)',  # Java: at com.Class(File.java:123)
            r'File\s+"([^"]+)",\s+line\s+(\d+)',  # Python: File "script.py", line 123
            r'([\w.]+):(\d+):(\d+)',  # JavaScript/TypeScript: file.js:123:45
            r'([\w.]+\.cs):line\s+(\d+)',  # C#: File.cs:line 123
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, stack_trace)
            for match in matches:
                filename = match[0].split('/')[-1].split('\\')[-1]
                line_number = match[1] if len(match) > 1 else "?"
                
                if filename in self.file_index and self.file_index[filename] not in seen_paths:
                    file_path = self.file_index[filename]
                    content = self._read_file_excerpt(file_path, int(line_number) if line_number.isdigit() else None)
                    
                    relevant_files.append({
                        'path': file_path,
                        'filename': filename,
                        'line': line_number,
                        'content': content,
                        'relevance': 'stack_trace'
                    })
                    seen_paths.add(file_path)
        
        # 2. Extract class names from error message
        words = re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', error_message)
        for word in words:
            if word in self.class_index:
                for file_path in self.class_index[word][:2]:  # Take first 2 matches
                    if file_path not in seen_paths:
                        content = self._read_file_excerpt(file_path)
                        relevant_files.append({
                            'path': file_path,
                            'filename': Path(file_path).name,
                            'line': '?',
                            'content': content,
                            'relevance': 'class_match'
                        })
                        seen_paths.add(file_path)
        
        return relevant_files[:max_files]
    
    def _read_file_excerpt(self, file_path: str, line_number: Optional[int] = None, context_lines: int = 10) -> str:
        """Read relevant section from file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if line_number and 0 < line_number <= len(lines):
                # Context around specific line
                start = max(0, line_number - context_lines - 1)
                end = min(len(lines), line_number + context_lines)
                excerpt = ''.join(lines[start:end])
                return f"... (lines {start+1}-{end}) ...\n{excerpt}"
            else:
                # First N lines of the file
                excerpt = ''.join(lines[:20])
                return f"... (first 20 lines) ...\n{excerpt}"
        except Exception as e:
            return f"[Error reading file: {e}]"
    
    def get_file_content(self, file_path: str) -> str:
        """Returns the full file content"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"[Error reading file: {e}]"

class LogAnalyzerAgent(BaseAgent):
    """Agent that analyzes ELK logs"""
    
    def __init__(self):
        super().__init__("LogAnalyzer")
    
    async def analyze_logs(self, elk_logs_json: List[Dict[str, Any]]) -> LogAnalysis:
        """Analyze ELK logs"""
        self.log("Analyzing ELK logs...")
        
        prompt = f"""
        Aşağıdaki ELK loglarını analiz et ve şu bilgileri çıkar:
        
        1. Hata tipi (örn: NullPointerException, 404, TimeoutError, etc.)
        2. Hata mesajı
        3. Stack trace
        4. Etkilenen dosyalar (eğer varsa)
        5. Severity (critical, high, medium, low)
        
        ELK Logları:
        {json.dumps(elk_logs_json, indent=2, ensure_ascii=False)}
        
        Yanıtını sadece JSON formatında ver:
        {{
            "error_type": "...",
            "error_message": "...",
            "stack_trace": "...",
            "affected_files": [...],
            "severity": "..."
        }}
        
        SADECE JSON DÖNDÜR, BAŞKA BİR ŞEY YAZMA.
        """
        
        response = await self.call_claude(prompt)
        
        # JSON parse et
        try:
            # Markdown kod bloklarını temizle
            clean_response = response.replace('```json\n', '').replace('```json', '').replace('```\n', '').replace('```', '').strip()
            
            # Eğer yanıt bir liste ise ilk elemanı al
            data = json.loads(clean_response)
            if isinstance(data, list):
                data = data[0] if len(data) > 0 else {}
            
            # Gerekli alanları kontrol et
            if not isinstance(data, dict):
                self.log(f"⚠️  Unexpected response format. Raw response: {response[:200]}")
                raise ValueError("API yanıtı sözlük formatında değil")
            
            analysis = LogAnalysis(
                error_type=data.get('error_type', 'Unknown Error'),
                error_message=data.get('error_message', 'No message'),
                stack_trace=data.get('stack_trace', 'No stack trace'),
                affected_files=data.get('affected_files', []),
                severity=data.get('severity', 'medium'),
                timestamp=datetime.now().isoformat()
            )
            
            self.log(f"Analysis completed: {analysis.error_type} ({analysis.severity})")
            return analysis
            
        except json.JSONDecodeError as e:
            self.log(f"❌ JSON parse hatası: {e}")
            self.log(f"Raw response: {response[:500]}")
            raise
        except Exception as e:
            self.log(f"❌ Analysis error: {e}")
            self.log(f"Raw response: {response[:500]}")
            raise


class ErrorLocatorAgent(BaseAgent):
    """Agent that analyzes stack trace and exception messages to localize error source"""
    
    def __init__(self):
        super().__init__("ErrorLocator")
    
    async def locate_error(self, analysis: LogAnalysis, codebase_provider: Optional['CodebaseProvider'] = None) -> ErrorContext:
        """
        Stacktrace'i analiz ederek hatanın muhtemel kaynağını ve kök nedeni belirler.
        RAG yaklaşımı ile sadece ilgili dosyaları analiz eder.
        
        Args:
            analysis: LogAnalyzerAgent'tan gelen log analiz sonuçları
            codebase_provider: Codebase'i indexleyen ve ilgili dosyaları getiren provider
            
        Returns:
            ErrorContext: Hata lokasyonu, kök neden ve ilgili kod parçaları
        """
        self.log(f"Detecting error source for '{analysis.error_type}'...")
        
        # RAG: İlgili dosyaları bul
        relevant_files_info = ""
        relevant_file_paths = []
        
        if codebase_provider:
            self.log("Searching relevant files via RAG...")
            relevant_files = codebase_provider.find_relevant_files(
                analysis.stack_trace, 
                analysis.error_message,
                max_files=10
            )
            
            if relevant_files:
                self.log(f"  Found {len(relevant_files)} relevant files")
                relevant_files_info = "\n\nİlgili Dosyalar:\n"
                for idx, file_info in enumerate(relevant_files, 1):
                    relevant_files_info += f"\n{idx}. {file_info['filename']} (satır {file_info['line']}) - {file_info['relevance']}\n"
                    relevant_files_info += f"{file_info['content'][:500]}...\n"  # İlk 500 karakter
                    relevant_file_paths.append(file_info['path'])
            else:
                self.log("  ⚠️ No relevant files found")
        
            prompt = f"""
            Aşağıdaki hata bilgilerini analiz et ve hatanın kaynağını lokalize et:

            Error Type: {analysis.error_type}
            Error Message: {analysis.error_message}
            Severity: {analysis.severity}

            Stack Trace:
            {analysis.stack_trace}
            {relevant_files_info}

            Your task:
            1. Analyze the stack trace line by line
            2. Determine which file, class, method, and line the error occurred in
            3. Analyze code snippets from the relevant files above
            4. Identify the probable root cause
            5. Prepare a high-level summary

            Respond in JSON format:
            {{
                "error_location": "Exact error location (file:line:method format)",
                "root_cause": "Probable root cause - detailed analysis",
                "relevant_code": "Most critical code snippet from stack trace and its context (~10 lines)",
                "summary": "High-level summary of the error - 2-3 sentences"
            }}

            RETURN ONLY JSON.
            """
        
        response = await self.call_claude(prompt, max_tokens=3000)
        
        try:
            clean_response = response.replace('```json\n', '').replace('```json', '').replace('```\n', '').replace('```', '').strip()
            data = json.loads(clean_response)
            
            if isinstance(data, list):
                data = data[0] if len(data) > 0 else {}
            
            if not isinstance(data, dict):
                raise ValueError("API yanıtı sözlük formatında değil")
            
            error_context = ErrorContext(
                error_location=data.get('error_location', 'Unknown'),
                root_cause=data.get('root_cause', 'Unknown'),
                relevant_code=data.get('relevant_code', 'N/A'),
                summary=data.get('summary', 'No summary available'),
                relevant_files=relevant_file_paths
            )
            
            self.log(f"Error localized: {error_context.error_location}")
            self.log(f"Root cause: {error_context.root_cause[:100]}...")
            
            return error_context
            
        except json.JSONDecodeError as e:
            self.log(f"❌ JSON parse hatası: {e}")
            self.log(f"Raw response: {response[:500]}")
            raise
        except Exception as e:
            self.log(f"❌ Localization error: {e}")
            self.log(f"Raw response: {response[:500]}")
            raise
    
    def _extract_stacktrace_locations(self, stack_trace: str) -> List[str]:
        """
        Stack trace'ten dosya lokasyonlarını çıkarır.
        
        Args:
            stack_trace: Stack trace string'i
            
        Returns:
            Dosya:satır formatında lokasyon listesi
        """
        import re
        
        # Farklı dillerdeki stack trace formatlarını yakala
        patterns = [
            r'at\s+[\w.]+\(([\w.]+):(\d+)\)',  # Java: at com.Class(File.java:123)
            r'File\s+"([^"]+)",\s+line\s+(\d+)',  # Python: File "script.py", line 123
            r'(\w+\.\w+):(\d+):\d+',  # JavaScript: file.js:123:45
        ]
        
        locations = []
        for pattern in patterns:
            matches = re.findall(pattern, stack_trace)
            for match in matches:
                locations.append(f"{match[0]}:{match[1]}")
        
        return locations[:5]  # İlk 5 lokasyonu döndür


class SolutionArchitectAgent(BaseAgent):
    """Çözüm öneren agent"""
    
    def __init__(self):
        super().__init__("SolutionArchitect")
    
    async def propose_solution(self, analysis: LogAnalysis, error_context: ErrorContext = None, codebase_context: str = "") -> Solution:
        """Hataya çözüm önerir"""
        self.log(f"Generating solution for '{analysis.error_type}'...")
        
        # ErrorContext varsa onu kullan
        context_info = ""
        if error_context:
            context_info = f"""
        Hata Lokasyonu: {error_context.error_location}
        Kök Neden: {error_context.root_cause}
        İlgili Kod: {error_context.relevant_code}
        Özet: {error_context.summary}
        """
        
        prompt = f"""
        Aşağıdaki hata için çözüm öner:
        
        Hata Tipi: {analysis.error_type}
        Hata Mesajı: {analysis.error_message}
        Etkilenen Dosyalar: {', '.join(analysis.affected_files) if analysis.affected_files else 'Bilinmiyor'}
        Severity: {analysis.severity}
        
        Stack Trace:
        {analysis.stack_trace}
        
        {context_info}
        
        {f"Kod Bağlamı: {codebase_context}" if codebase_context else ""}
        
        Çözüm önerini JSON formatında ver:
        {{
            "description": "Çözümün detaylı açıklaması",
            "affected_files": ["dosya1.py", "dosya2.py"],
            "code_changes": {{
                "dosya1.py": "Yapılacak değişikliğin açıklaması",
                "dosya2.py": "Yapılacak değişikliğin açıklaması"
            }},
            "tests_needed": ["test1_açıklaması", "test2_açıklaması"]
        }}
        
        SADECE JSON DÖNDÜR.
        """
        
        response = await self.call_claude(prompt, max_tokens=3000)
        
        try:
            clean_response = response.replace('```json\n', '').replace('```json', '').replace('```\n', '').replace('```', '').strip()
            data = json.loads(clean_response)
            
            if isinstance(data, list):
                data = data[0] if len(data) > 0 else {}
            
            if not isinstance(data, dict):
                raise ValueError("API yanıtı sözlük formatında değil")
            
            solution = Solution(
                description=data.get('description', 'No description'),
                affected_files=data.get('affected_files', []),
                code_changes=data.get('code_changes', {}),
                tests_needed=data.get('tests_needed', [])
            )
            
            self.log(f"Solution ready: {len(solution.affected_files)} files will be affected")
            return solution
            
        except json.JSONDecodeError as e:
            self.log(f"❌ JSON parse hatası: {e}")
            self.log(f"Raw response: {response[:500]}")
            raise
        except Exception as e:
            self.log(f"❌ Solution generation error: {e}")
            self.log(f"Raw response: {response[:500]}")
            raise


class CodeGeneratorAgent(BaseAgent):
    """Agent that implements code changes"""
    
    def __init__(self):
        super().__init__("CodeGenerator")
    
    async def generate_fix(self, solution: Solution, file_contents: Dict[str, str], codebase_provider: Optional[CodebaseProvider] = None, save_changes_callback=None) -> Dict[str, str]:
        """Implement solution as code"""
        self.log("Generating code changes...")
        
        fixed_files = {}
        
        for file_path in solution.affected_files:
            self.log(f"  Fixing {file_path}...")
            
            # Önce file_contents'ten bak, yoksa codebase_provider'dan oku
            original_content = file_contents.get(file_path, "")
            
            if not original_content and codebase_provider:
                # Tam dosya yolunu bul
                filename = os.path.basename(file_path)
                if filename in codebase_provider.file_index:
                    full_path = codebase_provider.file_index[filename]
                    original_content = codebase_provider.get_file_content(full_path)
                    self.log(f"    File read: {full_path}")
            
            if not original_content:
                self.log(f"  ⚠️  {file_path} content not found, skipping...")
                continue
            
            change_description = solution.code_changes.get(file_path, "")
            
            prompt = f"""
            Aşağıdaki dosyayı düzelt:
            
            Dosya: {file_path}
            Yapılacak Değişiklik: {change_description}
            
            Genel Çözüm: {solution.description}
            
            Mevcut Kod:
            ```
            {original_content}
            ```
            
            Düzeltilmiş kodun TAMAMINI döndür. Sadece kodu döndür, açıklama yazma.
            """
            
            fixed_content = await self.call_claude(prompt, max_tokens=4000)
            
            # Kod bloklarını temizle
            fixed_content = fixed_content.replace('```python\n', '').replace('```javascript\n', '').replace('```java\n', '').replace('```csharp\n', '').replace('```cs\n', '').replace('```\n', '').replace('```', '').strip()
            
            # Dosya adını key olarak kullan (tam path değil)
            fixed_files[file_path] = fixed_content
        
        self.log(f"Fixed {len(fixed_files)} files")
        return fixed_files


class GitManagerAgent(BaseAgent):
    """Git işlemlerini yöneten agent"""
    
    def __init__(self, repo_path: str = "."):
        super().__init__("GitManager")
        self.repo_path = repo_path
    
    async def create_fix_branch(self, analysis: LogAnalysis, fixed_files: Dict[str, str], codebase_provider: Optional['CodebaseProvider'] = None) -> GitOperation:
        """Fix için branch oluşturur ve commit eder"""
        self.log("Creating Git branch...")
        
        import subprocess
        
        # Branch ismi oluştur
        error_slug = analysis.error_type.lower().replace(' ', '-').replace('_', '-')
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        branch_name = f"fix/{error_slug}-{timestamp}"
        
        try:
            # Yeni branch oluştur
            subprocess.run(['git', 'checkout', '-b', branch_name], 
                         cwd=self.repo_path, check=True, capture_output=True)
            self.log(f"Branch created: {branch_name}")
            
            # Dosyaları yaz
            for file_path, content in fixed_files.items():
                # Tam dosya yolunu bul
                full_path = None
                
                if codebase_provider:
                    filename = os.path.basename(file_path)
                    if filename in codebase_provider.file_index:
                        full_path = codebase_provider.file_index[filename]
                        self.log(f"  Hedef dosya: {full_path}")
                
                # Eğer tam yol bulunamazsa, dosya ismini repo_path'e ekle
                if not full_path:
                    full_path = os.path.join(self.repo_path, file_path)
                
                # Dizini oluştur
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Dosyayı yaz
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.log(f"  ✓ {os.path.basename(full_path)} written")
            
            # Git add - tüm değişiklikleri ekle
            subprocess.run(['git', 'add', '-A'], 
                         cwd=self.repo_path, check=True, capture_output=True)
            
            # Commit edilecek değişiklik var mı kontrol et
            status_result = subprocess.run(['git', 'status', '--porcelain'], 
                         cwd=self.repo_path, capture_output=True, text=True)
            
            if not status_result.stdout.strip():
                self.log("⚠ No changes to commit, deleting branch...")
                subprocess.run(['git', 'checkout', '-'], cwd=self.repo_path, capture_output=True)
                subprocess.run(['git', 'branch', '-D', branch_name], cwd=self.repo_path, capture_output=True)
                return GitOperation(
                    branch_name="",
                    commit_message="No changes to commit",
                    files_changed=[],
                    success=False
                )
            
            # Commit mesajı oluştur
            commit_message = f"""Fix: {analysis.error_type}

{analysis.error_message}

Severity: {analysis.severity}
Auto-generated fix by AI Agent System
Timestamp: {analysis.timestamp}
"""
            
            # Commit
            result = subprocess.run(['git', 'commit', '-m', commit_message], 
                         cwd=self.repo_path, capture_output=True, text=True)
            
            if result.returncode != 0:
                self.log(f"Git commit error: {result.stderr}")
                # If git config is missing, inform user
                if 'user.name' in result.stderr or 'user.email' in result.stderr:
                    self.log("Git config missing! Set git user information:")
                    self.log("  git config user.name 'Your Name'")
                    self.log("  git config user.email 'your.email@example.com'")
                raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
            
            self.log("Changes committed")
            
            return GitOperation(
                branch_name=branch_name,
                commit_message=commit_message,
                files_changed=list(fixed_files.keys()),
                success=True
            )
            
        except subprocess.CalledProcessError as e:
            self.log(f"Git error: {e}")
            return GitOperation(
                branch_name=branch_name,
                commit_message="",
                files_changed=[],
                success=False
            )


class Orchestrator:
    """Tüm agent'ları koordine eden ana sınıf"""
    
    def __init__(self, repo_path: str = ".", enable_rag: bool = True):
        self.log_analyzer = LogAnalyzerAgent()
        self.error_locator = ErrorLocatorAgent()
        self.solution_architect = SolutionArchitectAgent()
        self.code_generator = CodeGeneratorAgent()
        self.git_manager = GitManagerAgent(repo_path)
        self.codebase_provider = CodebaseProvider(repo_path) if enable_rag else None
        
        if self.codebase_provider:
            print(f"📚 Codebase indexed: {len(self.codebase_provider.file_index)} files, {len(self.codebase_provider.class_index)} classes")
    
    async def process_logs(self, elk_logs_json: List[Dict[str, Any]], file_contents: Dict[str, str] = None, codebase_context: str = "", save_changes_callback=None) -> GitOperation:
        """Ana workflow - logları işler ve fix oluşturur
        
        Args:
            elk_logs_json: ELK'den gelen log listesi
            file_contents: Dosya içerikleri
            codebase_context: Ek bağlam bilgisi
            save_changes_callback: Kod değişikliklerini kaydetmek için callback fonksiyonu
        """
        print("\n" + "="*80)
        print("🤖 Multi-Agent Log Fix System Başlatıldı")
        print("="*80 + "\n")
        
        # 0. Adım: Log Filtreleme
        selected_log = elk_logs_json
        
        if not selected_log:
            print("\n⚠️  Hedef hata tipi bulunamadı. İşlem sonlandırılıyor.")
            return GitOperation(
                branch_name="",
                commit_message="",
                files_changed=[],
                success=False
            )
        
        # 1. Adım: Log Analizi
        analysis = await self.log_analyzer.analyze_logs(selected_log)
        
        print(f"\n📊 Analiz Sonuço:")
        print(f"   Hata: {analysis.error_type}")
        print(f"   Severity: {analysis.severity}")
        print(f"   Etkilenen dosyalar: {', '.join(analysis.affected_files) if analysis.affected_files else 'Bilinmiyor'}")
        
        # 2. Adım: Hata Lokalizasyonu (RAG ile)
        error_context = await self.error_locator.locate_error(analysis, self.codebase_provider)
        
        print(f"\n🎯 Hata Lokasyonu:")
        print(f"   Lokasyon: {error_context.error_location}")
        print(f"   Root Cause: {error_context.root_cause[:100]}...")
        print(f"   Summary: {error_context.summary}")
        if error_context.relevant_files:
            print(f"   Relevant Files: {len(error_context.relevant_files)} files")
        
        # 3. Adım: Çözüm Önerisi
        solution = await self.solution_architect.propose_solution(analysis, error_context, codebase_context)
        
        print(f"\n💡 Proposed Solution:")
        print(f"   {solution.description}")
        print(f"   Files to Change: {', '.join(solution.affected_files) if solution.affected_files else 'None'}")
        
        # Eğer değiştirilecek dosya yoksa dur
        if not solution.affected_files or len(solution.affected_files) == 0:
            print(f"\n⚠️  No files to change. Terminating operation.")
            return GitOperation(
                branch_name="",
                commit_message="",
                files_changed=[],
                success=False
            )
        
        # 4. Adım: Kod Üretimi
        if file_contents is None:
            file_contents = {}
            
        fixed_files = await self.code_generator.generate_fix(solution, file_contents, self.codebase_provider)
        
        # Orijinal dosyaları oku ve callback'e gönder (UI için)
        if save_changes_callback and self.codebase_provider:
            for file_path in fixed_files.keys():
                filename = os.path.basename(file_path)
                if filename in self.codebase_provider.file_index:
                    original_path = self.codebase_provider.file_index[filename]
                    original_content = self.codebase_provider.get_file_content(original_path)
                    save_changes_callback(filename, original_content, fixed_files[file_path])
        
        # Eğer düzeltilmiş dosya yoksa dur
        if not fixed_files or len(fixed_files) == 0:
            print(f"\n⚠️  0 files fixed. Skipping Git operations.")
            return GitOperation(
                branch_name="",
                commit_message="",
                files_changed=[],
                success=False
            )
        
        print(f"\n✏️  Code Changes:")
        for file_path in fixed_files.keys():
            print(f"   ✓ {file_path}")
        
        # 5. Adım: Git İşlemleri
        git_result = await self.git_manager.create_fix_branch(analysis, fixed_files, self.codebase_provider)
        
        if git_result.success:
            print(f"\n🎉 Operation Successful!")
            print(f"   Branch: {git_result.branch_name}")
            print(f"   Files changed: {len(git_result.files_changed)}")
        else:
            print(f"\n❌ Git operation failed")
        
        print("\n" + "="*80 + "\n")
        
        return git_result


# Async çalıştırma helper
async def main():
    """Fetches logs from real ELK and analyzes them"""
    from elk_connector import create_elk_connector

    # ELK connection (real or mock)
    # To use real ELK: use_mock=False, host="your-elk-host", port=9200
    elk = create_elk_connector(
        use_mock=False,  # Use real ELK
        host=os.getenv("ELK_HOST", "localhost"),
        port=int(os.getenv("ELK_PORT", "9200")),
        username=os.getenv("ELK_USERNAME"),
        password=os.getenv("ELK_PASSWORD")
    )

    # Connect to ELK
    if not elk.connect():
        print("❌ Could not connect to ELK. Continuing with mock data...")
        elk = create_elk_connector(use_mock=True)
        elk.connect()

    # Fetch errors from the last 180 minutes
    print("\n📡 Fetching logs from ELK...")
    elk_logs_list = elk.fetch_error_logs(time_range_minutes=180)

    if not elk_logs_list or len(elk_logs_list) == 0:
        print("❌ No error logs found in ELK. Terminating operation.")
        print("   Please make sure there are ERROR level logs in ELK.")
        return None

    print(f"✓ {len(elk_logs_list)} logs found")

    # Codebase path - Your project
    repo_path = r"C:\Users\AhmetBolat\Projects\Claude\TestSystem"

    print(f"\n📂 Codebase: {repo_path}")

    # Start the Orchestrator (indexes codebase with RAG)
    orchestrator = Orchestrator(
        repo_path=repo_path,
        enable_rag=True
    )

    # Automatically get file contents (RAG will find relevant files)
    file_contents = {}

    # Process logs (as a JSON list)
    result = await orchestrator.process_logs(elk_logs_list, file_contents)

    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
