"""Add legal page translations to locale files."""
import json
import os

# Legal page translations
legal_translations = {
    'ko': {
        'legal': {
            'terms': {
                'title': '이용약관',
                'last_updated': '최종 수정일: 2024년 12월 23일',
                'sections': [
                    {
                        'title': '제1조 (목적)',
                        'content': '이 약관은 Creator Control Center(이하 "회사")가 제공하는 서비스의 이용조건 및 절차, 회사와 회원의 권리, 의무 및 책임사항을 규정함을 목적으로 합니다.'
                    },
                    {
                        'title': '제2조 (정의)',
                        'content': '1. "서비스"란 회사가 제공하는 크리에이터 채널 관리 및 분석 서비스를 말합니다.\n2. "회원"이란 이 약관에 동의하고 서비스를 이용하는 자를 말합니다.\n3. "계정"이란 회원이 서비스 이용을 위해 생성한 고유 식별 정보를 말합니다.'
                    },
                    {
                        'title': '제3조 (약관의 효력 및 변경)',
                        'content': '1. 이 약관은 서비스 화면에 게시하거나 기타 방법으로 회원에게 공지함으로써 효력이 발생합니다.\n2. 회사는 필요한 경우 이 약관을 변경할 수 있으며, 변경된 약관은 제1항과 같은 방법으로 공지함으로써 효력이 발생합니다.'
                    },
                    {
                        'title': '제4조 (서비스의 제공)',
                        'content': '1. 회사는 다음의 서비스를 제공합니다:\n   - 소셜 미디어 채널 통합 관리\n   - 채널 성과 분석 및 리포팅\n   - AI 기반 인사이트 제공\n2. 서비스는 연중무휴, 1일 24시간 제공함을 원칙으로 합니다.'
                    },
                    {
                        'title': '제5조 (회원의 의무)',
                        'content': '1. 회원은 관계법령, 이 약관의 규정, 이용안내 등을 준수하여야 합니다.\n2. 회원은 타인의 개인정보를 도용하거나 서비스를 부정하게 이용해서는 안 됩니다.\n3. 회원은 계정 정보의 보안을 유지할 책임이 있습니다.'
                    },
                    {
                        'title': '제6조 (지적재산권)',
                        'content': '서비스 및 관련 콘텐츠에 대한 저작권 및 지적재산권은 회사에 귀속됩니다. 회원은 회사의 사전 동의 없이 이를 복제, 배포, 방송 또는 기타 방법으로 이용할 수 없습니다.'
                    },
                    {
                        'title': '제7조 (면책조항)',
                        'content': '1. 회사는 천재지변, 전쟁 등 불가항력적 사유로 인한 서비스 중단에 대해 책임을 지지 않습니다.\n2. 회사는 회원의 귀책사유로 인한 서비스 이용 장애에 대해 책임을 지지 않습니다.'
                    },
                    {
                        'title': '제8조 (분쟁해결)',
                        'content': '이 약관에 관한 분쟁은 대한민국 법률에 따라 해결하며, 관할 법원은 회사 소재지 관할 법원으로 합니다.'
                    }
                ]
            },
            'privacy': {
                'title': '개인정보처리방침',
                'last_updated': '최종 수정일: 2024년 12월 23일',
                'sections': [
                    {
                        'title': '1. 수집하는 개인정보',
                        'content': '회사는 서비스 제공을 위해 다음의 개인정보를 수집합니다:\n- 필수: 이메일 주소, 비밀번호(암호화 저장)\n- 선택: 이름, 프로필 사진\n- 소셜 로그인 시: 해당 플랫폼 ID, 이메일, 프로필 정보'
                    },
                    {
                        'title': '2. 개인정보의 수집 및 이용목적',
                        'content': '- 회원 가입 및 관리\n- 서비스 제공 및 개선\n- 고객 지원 및 문의 응대\n- 법적 의무 이행'
                    },
                    {
                        'title': '3. 개인정보의 보유 및 이용기간',
                        'content': '회원 탈퇴 시 또는 수집 목적 달성 시 지체 없이 파기합니다. 단, 관계법령에 따라 보존이 필요한 경우 해당 기간 동안 보관합니다.'
                    },
                    {
                        'title': '4. 개인정보의 제3자 제공',
                        'content': '회사는 회원의 동의 없이 개인정보를 제3자에게 제공하지 않습니다. 다만, 법령에 따른 요청이 있는 경우는 예외로 합니다.'
                    },
                    {
                        'title': '5. 개인정보의 안전성 확보조치',
                        'content': '- 비밀번호 암호화 저장\n- SSL/TLS 통신 암호화\n- 접근 권한 관리\n- 정기적인 보안 점검'
                    },
                    {
                        'title': '6. 정보주체의 권리',
                        'content': '회원은 언제든지 자신의 개인정보에 대해 열람, 정정, 삭제, 처리정지를 요청할 수 있습니다. 요청은 설정 페이지 또는 고객지원을 통해 가능합니다.'
                    },
                    {
                        'title': '7. 쿠키 사용',
                        'content': '회사는 서비스 이용 편의 및 분석을 위해 쿠키를 사용합니다. 브라우저 설정을 통해 쿠키 사용을 거부할 수 있습니다.'
                    },
                    {
                        'title': '8. 개인정보 보호책임자',
                        'content': '개인정보 관련 문의: hello@creatorcontrol.center'
                    }
                ]
            },
            'contact': {
                'title': '문의하기',
                'subtitle': '궁금한 점이 있으시면 언제든 연락해 주세요.',
                'form': {
                    'name': '이름',
                    'email': '이메일',
                    'subject': '제목',
                    'message': '메시지',
                    'submit': '보내기',
                    'success': '메시지가 성공적으로 전송되었습니다.',
                    'error': '메시지 전송에 실패했습니다. 다시 시도해 주세요.'
                },
                'info': {
                    'title': '연락처 정보',
                    'email': 'hello@creatorcontrol.center',
                    'response_time': '영업일 기준 24시간 이내 답변 드립니다.'
                }
            }
        }
    },
    'en': {
        'legal': {
            'terms': {
                'title': 'Terms of Service',
                'last_updated': 'Last Updated: December 23, 2024',
                'sections': [
                    {
                        'title': 'Article 1 (Purpose)',
                        'content': 'These Terms govern the conditions and procedures for using the services provided by Creator Control Center (hereinafter "Company"), and define the rights, obligations, and responsibilities of the Company and its members.'
                    },
                    {
                        'title': 'Article 2 (Definitions)',
                        'content': '1. "Service" refers to the creator channel management and analytics service provided by the Company.\n2. "Member" refers to a person who agrees to these Terms and uses the Service.\n3. "Account" refers to unique identification information created by a member for using the Service.'
                    },
                    {
                        'title': 'Article 3 (Effect and Amendment of Terms)',
                        'content': '1. These Terms take effect when posted on the Service screen or notified to members by other means.\n2. The Company may amend these Terms when necessary, and amended Terms take effect when notified in the same manner as paragraph 1.'
                    },
                    {
                        'title': 'Article 4 (Provision of Service)',
                        'content': '1. The Company provides the following services:\n   - Integrated social media channel management\n   - Channel performance analytics and reporting\n   - AI-based insights\n2. The Service is provided 24 hours a day, year-round, in principle.'
                    },
                    {
                        'title': 'Article 5 (Member Obligations)',
                        'content': '1. Members must comply with relevant laws, these Terms, and usage guidelines.\n2. Members must not misappropriate others\' personal information or fraudulently use the Service.\n3. Members are responsible for maintaining the security of their account information.'
                    },
                    {
                        'title': 'Article 6 (Intellectual Property Rights)',
                        'content': 'Copyrights and intellectual property rights for the Service and related content belong to the Company. Members may not reproduce, distribute, broadcast, or otherwise use them without prior consent from the Company.'
                    },
                    {
                        'title': 'Article 7 (Disclaimer)',
                        'content': '1. The Company is not liable for service interruptions due to force majeure such as natural disasters or wars.\n2. The Company is not liable for service disruptions caused by members\' own fault.'
                    },
                    {
                        'title': 'Article 8 (Dispute Resolution)',
                        'content': 'Disputes regarding these Terms shall be resolved in accordance with the laws of the Republic of Korea, and the competent court shall be the court having jurisdiction over the Company\'s location.'
                    }
                ]
            },
            'privacy': {
                'title': 'Privacy Policy',
                'last_updated': 'Last Updated: December 23, 2024',
                'sections': [
                    {
                        'title': '1. Personal Information Collected',
                        'content': 'The Company collects the following personal information to provide services:\n- Required: Email address, password (encrypted)\n- Optional: Name, profile photo\n- For social login: Platform ID, email, profile information'
                    },
                    {
                        'title': '2. Purpose of Collection and Use',
                        'content': '- Member registration and management\n- Service provision and improvement\n- Customer support and inquiry response\n- Legal compliance'
                    },
                    {
                        'title': '3. Retention Period',
                        'content': 'Personal information is destroyed without delay upon member withdrawal or when the purpose of collection is achieved. However, if retention is required by relevant laws, it is stored for the required period.'
                    },
                    {
                        'title': '4. Provision to Third Parties',
                        'content': 'The Company does not provide personal information to third parties without member consent. However, requests pursuant to laws are exceptions.'
                    },
                    {
                        'title': '5. Security Measures',
                        'content': '- Password encryption\n- SSL/TLS communication encryption\n- Access control management\n- Regular security audits'
                    },
                    {
                        'title': '6. Data Subject Rights',
                        'content': 'Members may request access, correction, deletion, or suspension of processing of their personal information at any time. Requests can be made through settings or customer support.'
                    },
                    {
                        'title': '7. Cookie Usage',
                        'content': 'The Company uses cookies for service convenience and analytics. You can refuse cookie usage through browser settings.'
                    },
                    {
                        'title': '8. Privacy Officer',
                        'content': 'For privacy inquiries: hello@creatorcontrol.center'
                    }
                ]
            },
            'contact': {
                'title': 'Contact Us',
                'subtitle': 'Have questions? Feel free to reach out anytime.',
                'form': {
                    'name': 'Name',
                    'email': 'Email',
                    'subject': 'Subject',
                    'message': 'Message',
                    'submit': 'Send',
                    'success': 'Your message has been sent successfully.',
                    'error': 'Failed to send message. Please try again.'
                },
                'info': {
                    'title': 'Contact Information',
                    'email': 'hello@creatorcontrol.center',
                    'response_time': 'We respond within 24 business hours.'
                }
            }
        }
    },
    'ja': {
        'legal': {
            'terms': {
                'title': '利用規約',
                'last_updated': '最終更新日：2024年12月23日',
                'sections': [
                    {
                        'title': '第1条（目的）',
                        'content': 'この規約は、Creator Control Center（以下「当社」）が提供するサービスの利用条件および手続き、当社と会員の権利、義務および責任事項を規定することを目的とします。'
                    },
                    {
                        'title': '第2条（定義）',
                        'content': '1. 「サービス」とは、当社が提供するクリエイターチャンネル管理および分析サービスを指します。\n2. 「会員」とは、この規約に同意しサービスを利用する者を指します。\n3. 「アカウント」とは、会員がサービス利用のために作成した固有の識別情報を指します。'
                    },
                    {
                        'title': '第3条（規約の効力および変更）',
                        'content': '1. この規約は、サービス画面に掲示またはその他の方法で会員に通知することにより効力が発生します。\n2. 当社は必要な場合にこの規約を変更することができ、変更された規約は第1項と同様の方法で通知することにより効力が発生します。'
                    },
                    {
                        'title': '第4条（サービスの提供）',
                        'content': '1. 当社は以下のサービスを提供します：\n   - ソーシャルメディアチャンネルの統合管理\n   - チャンネルパフォーマンス分析とレポーティング\n   - AIベースのインサイト提供\n2. サービスは原則として年中無休、24時間提供されます。'
                    },
                    {
                        'title': '第5条（会員の義務）',
                        'content': '1. 会員は関係法令、この規約の規定、利用ガイドなどを遵守しなければなりません。\n2. 会員は他人の個人情報を盗用したり、サービスを不正に利用してはなりません。\n3. 会員はアカウント情報のセキュリティを維持する責任があります。'
                    },
                    {
                        'title': '第6条（知的財産権）',
                        'content': 'サービスおよび関連コンテンツに対する著作権および知的財産権は当社に帰属します。会員は当社の事前同意なしにこれを複製、配布、放送またはその他の方法で利用することはできません。'
                    },
                    {
                        'title': '第7条（免責事項）',
                        'content': '1. 当社は天災地変、戦争など不可抗力的事由によるサービス中断について責任を負いません。\n2. 当社は会員の責に帰すべき事由によるサービス利用障害について責任を負いません。'
                    },
                    {
                        'title': '第8条（紛争解決）',
                        'content': 'この規約に関する紛争は大韓民国の法律に従って解決し、管轄裁判所は当社所在地の管轄裁判所とします。'
                    }
                ]
            },
            'privacy': {
                'title': 'プライバシーポリシー',
                'last_updated': '最終更新日：2024年12月23日',
                'sections': [
                    {
                        'title': '1. 収集する個人情報',
                        'content': '当社はサービス提供のため以下の個人情報を収集します：\n- 必須：メールアドレス、パスワード（暗号化保存）\n- 任意：氏名、プロフィール写真\n- ソーシャルログイン時：プラットフォームID、メール、プロフィール情報'
                    },
                    {
                        'title': '2. 収集・利用目的',
                        'content': '- 会員登録および管理\n- サービス提供および改善\n- カスタマーサポートおよびお問い合わせ対応\n- 法的義務の履行'
                    },
                    {
                        'title': '3. 保有期間',
                        'content': '会員退会時または収集目的達成時に遅滞なく破棄します。ただし、関係法令により保存が必要な場合は該当期間保管します。'
                    },
                    {
                        'title': '4. 第三者への提供',
                        'content': '当社は会員の同意なしに個人情報を第三者に提供しません。ただし、法令に基づく要請がある場合は例外とします。'
                    },
                    {
                        'title': '5. セキュリティ対策',
                        'content': '- パスワード暗号化\n- SSL/TLS通信暗号化\n- アクセス権限管理\n- 定期的なセキュリティ監査'
                    },
                    {
                        'title': '6. 情報主体の権利',
                        'content': '会員はいつでも自分の個人情報について閲覧、訂正、削除、処理停止を要請できます。要請は設定ページまたはカスタマーサポートを通じて可能です。'
                    },
                    {
                        'title': '7. Cookieの使用',
                        'content': '当社はサービス利用の利便性および分析のためにCookieを使用します。ブラウザ設定を通じてCookieの使用を拒否できます。'
                    },
                    {
                        'title': '8. 個人情報保護責任者',
                        'content': '個人情報に関するお問い合わせ：hello@creatorcontrol.center'
                    }
                ]
            },
            'contact': {
                'title': 'お問い合わせ',
                'subtitle': 'ご質問がございましたら、いつでもお気軽にご連絡ください。',
                'form': {
                    'name': 'お名前',
                    'email': 'メールアドレス',
                    'subject': '件名',
                    'message': 'メッセージ',
                    'submit': '送信',
                    'success': 'メッセージが正常に送信されました。',
                    'error': 'メッセージの送信に失敗しました。もう一度お試しください。'
                },
                'info': {
                    'title': 'お問い合わせ先',
                    'email': 'hello@creatorcontrol.center',
                    'response_time': '営業日24時間以内にご返答いたします。'
                }
            }
        }
    }
}

# Footer link translations
footer_links = {
    'ko': {
        'terms': '이용약관',
        'privacy': '개인정보처리방침',
        'contact_link': '문의하기'
    },
    'en': {
        'terms': 'Terms of Service',
        'privacy': 'Privacy Policy',
        'contact_link': 'Contact Us'
    },
    'ja': {
        'terms': '利用規約',
        'privacy': 'プライバシーポリシー',
        'contact_link': 'お問い合わせ'
    }
}

def main():
    locales_dir = os.path.join(os.path.dirname(__file__), '..', 'app', 'locales')

    for lang in ['ko', 'en', 'ja']:
        filepath = os.path.join(locales_dir, f'{lang}.json')
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Add legal section
        data['legal'] = legal_translations[lang]['legal']

        # Add footer legal links
        data['footer'].update(footer_links[lang])

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f'{lang}.json updated successfully')

    print('All locale files updated!')

if __name__ == '__main__':
    main()
