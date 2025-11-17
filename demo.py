#!/usr/bin/env python3
"""
Demo Script - Tests the AI Agent System
"""

import asyncio
import os
from orchestrator import Orchestrator
from elk_connector import MockELKConnector


async def demo():
    """Demo workflow"""
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         🤖 AI Multi-Agent System Demo                    ║
    ║                                                           ║
    ║  Bu demo, sistemin nasıl çalıştığını gösterir            ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    input("Press Enter to start the demo...")
    
    # 1. ELK Mock
    print("\n" + "="*80)
    print("STEP 1: Fetching sample error logs from Mock ELK...")
    print("="*80)
    
    elk = MockELKConnector()
    elk.connect()
    elk_logs = elk.get_recent_errors()
    
    print(f"\n✓ {len(elk_logs)} characters of log data received")
    print("\nSample log snippet:")
    print("-" * 80)
    print(elk_logs[:500] + "...")
    print("-" * 80)
    
    input("\nPress Enter to continue...")
    
    # 2. Örnek dosya içerikleri
    print("\n" + "="*80)
    print("STEP 2: Loading sample source code files...")
    print("="*80)
    
    sample_files = {
        "UserController.java": """package com.example.controller;

import com.example.service.UserService;
import com.example.model.User;

public class UserController {
    private UserService userService;
    
    public UserController() {
        // UserService dependency injection eksik!
    }
    
    public User getUser(Long id) {
        // Burada userService null olduğu için NullPointerException oluşur
        return userService.findById(id);
    }
    
    public void updateUser(Long id, User userData) {
        User existingUser = userService.findById(id);
        existingUser.setName(userData.getName());
        existingUser.setEmail(userData.getEmail());
        userService.save(existingUser);
    }
}
""",
        "UserService.java": """package com.example.service;

import com.example.model.User;
import com.example.repository.UserRepository;

public class UserService {
    private UserRepository userRepository;
    
    public UserService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }
    
    public User findById(Long id) {
        return userRepository.findById(id).orElse(null);
    }
    
    public void save(User user) {
        userRepository.save(user);
    }
}
"""
    }
    
    print("\n✓ 2 source files loaded:")
    for filename in sample_files.keys():
        print(f"  - {filename}")
    
    input("\nPress Enter to continue...")
    
    # 3. Orchestrator
    print("\n" + "="*80)
    print("STEP 3: Starting the Multi-Agent system...")
    print("="*80)
    print("\nAgent'lar sırasıyla çalışacak:")
    print("  1. 🔍 Log Analyzer - Will analyze logs")
    print("  2. 💡 Solution Architect - Will propose a solution")
    print("  3. ✏️  Code Generator - Will fix the code")
    print("  4. 🌿 Git Manager - Will create a branch")
    print("  3. ✏️  Code Generator - Kodu düzeltecek")
    input("\nPress Enter to start the analysis...")
    
    input("\nAnalizi başlatmak için Enter'a basın...")
    
    orchestrator = Orchestrator(repo_path=".")
    
    # 4. Analizi çalıştır
    try:
        result = await orchestrator.process_logs(elk_logs, sample_files)
        
        print("DEMO COMPLETED!")
        print("\n" + "="*80)
        print("DEMO TAMAMLANDI!")
        print("="*80)
        
        if result.success:
            print(f"""
✅ Başarılı!

Oluşturulan Branch: {result.branch_name}
Değiştirilen Dosyalar: {len(result.files_changed)}

Bu demo'da sistem:
1. ✓ ELK loglarını analiz etti
2. ✓ NullPointerException hatasını tespit etti
3. ✓ Dependency Injection çözümü önerdi
4. ✓ Kodu otomatik düzeltti
5. ✓ Git branch oluşturdu
- Gerçek kod dosyalarınızı düzeltir
- Otomatik PR oluşturabilir (opsiyonel)

Daha fazla bilgi için: python cli.py --help""")
            print("\n❌ An error occurred during the demo")
        else:
            print("\n❌ Demo sırasında bir hata oluştu")
        print(f"\n❌ Demo error: {e}")
    except Exception as e:
        print(f"\n❌ Demo hatası: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)


if __name__ == "__main__":
    try:
        print("\n\n⚠️  Demo canceled")
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo iptal edildi")
